import datetime

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status

from plugins.polio.models import VACCINES, Campaign, CampaignScope, CampaignType
from plugins.polio.tests.api.campaigns.dropdown.common import BASE_URL, CampaignDropdownAPIBase


class CampaignDropdownViewsAPITestCase(CampaignDropdownAPIBase):
    """The lightweight endpoint feeding campaign select inputs (Form A, Earmarked, VRF...): who
    sees what, which filters apply, in what order, and at what query cost."""

    def test_requires_authentication(self):
        """Stricter than the list endpoint, which allows anonymous reads for the embedded calendar."""
        response = self.client.get(BASE_URL)

        self.assertJSONResponse(response, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_cannot_bypass_with_account_id(self):
        """The list endpoint honours `account_id` for anonymous callers; the dropdown must not."""
        response = self.client.get(BASE_URL, {"account_id": self.account.pk})

        self.assertJSONResponse(response, status.HTTP_401_UNAUTHORIZED)

    def test_write_methods_are_not_exposed(self):
        self.client.force_authenticate(self.user)

        post_response = self.client.post(BASE_URL, data={}, format="json")
        delete_response = self.client.delete(BASE_URL)

        self.assertJSONResponse(post_response, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertJSONResponse(delete_response, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_of_another_account_only_sees_its_own_campaigns(self):
        other_user = self.create_user_with_profile(username="user-2", account=self.other_account)
        self.client.force_authenticate(other_user)

        received = self.get_obr_names()

        self.assertEqual(["Campaign-other-account"], received)

    def test_user_restricted_to_org_units_only_sees_campaigns_in_their_hierarchy(self):
        """`filter_for_user` restricts on country / initial_org_unit when the profile has org units."""
        campaign_2 = self.create_campaign(
            obr_name="Campaign-2",
            account=self.account,
            source_version=self.source_version,
            country_ou_type=self.country_type,
            district_ou_type=self.district_type,
            country_name="Country-2",
            district_name="District-2",
        )[0]
        restricted_user = self.create_user_with_profile(
            username="user-restricted", account=self.account, org_units=[campaign_2.country]
        )
        self.client.force_authenticate(restricted_user)

        received = self.get_obr_names()

        self.assertEqual(["Campaign-2"], received)

    def test_other_account_campaigns_are_not_visible(self):
        self.client.force_authenticate(self.user)

        received = self.get_obr_names()

        self.assertNotIn(self.other_campaign.obr_name, received)

    def test_campaign_types_of_another_accounts_campaign_are_not_returned(self):
        """CampaignType rows are global, so the only thing scoping them is the campaign they hang off."""
        self.client.force_authenticate(self.user)
        other_type = CampaignType.objects.create(name="Type-other-account")
        self.other_campaign.campaign_types.set([other_type])

        received = [
            campaign_type["name"] for campaign in self.get_payload() for campaign_type in campaign["campaign_types"]
        ]

        expected = [self.polio_type.name, self.measles_type.name]
        self.assertEqual(expected, received)

    def test_filtering_on_another_accounts_campaign_type_returns_nothing(self):
        """A global type id must not be a way to read across accounts."""
        self.client.force_authenticate(self.user)
        other_type = CampaignType.objects.create(name="Type-other-account")
        self.other_campaign.campaign_types.set([other_type])

        received = self.get_obr_names({"campaign_types": other_type.pk})

        self.assertEqual([], received)

    def test_country_name_filter(self):
        self.client.force_authenticate(self.user)

        received_matching = self.get_obr_names({"country__name": "Country-1"})
        received_not_matching = self.get_obr_names({"country__name": "Country-unknown"})

        self.assertEqual(["Campaign-1"], received_matching)
        self.assertEqual([], received_not_matching)

    def test_country_id_filter(self):
        """What the VRF form sends, since it holds the country id rather than its name."""
        self.client.force_authenticate(self.user)

        received = self.get_obr_names({"country__id__in": self.country.pk})

        self.assertEqual(["Campaign-1"], received)

    def test_show_test_filter(self):
        """Same semantics as the list endpoint: `filter_show_test` only runs when the param is sent."""
        self.client.force_authenticate(self.user)

        received_without_test = self.get_obr_names({"show_test": "false"})
        received_with_test = self.get_obr_names({"show_test": "true"})

        self.assertNotIn(self.test_campaign.obr_name, received_without_test)
        self.assertIn(self.test_campaign.obr_name, received_with_test)

    def test_campaign_types_filter(self):
        self.client.force_authenticate(self.user)

        received_on_polio = self.get_obr_names({"campaign_types": self.polio_type.pk})
        received_on_measles = self.get_obr_names({"campaign_types": self.measles_type.pk})

        self.assertEqual(["Campaign-1"], received_on_polio)
        self.assertEqual(["Campaign-measles"], received_on_measles)

    def test_has_scopes_filter(self):
        """A vaccine request needs a scope to resolve districts, so the VRF form asks for it."""
        self.client.force_authenticate(self.user)
        per_round = Campaign.objects.create(
            obr_name="Campaign-per-round-scopes", account=self.account, separate_scopes_per_round=True
        )

        received_with_scopes = self.get_obr_names({"has_scopes": "true"})
        received_without_scopes = self.get_obr_names({"has_scopes": "false"})

        self.assertCountEqual(["Campaign-1", per_round.obr_name], received_with_scopes)
        self.assertCountEqual(
            ["Campaign-measles", "Campaign-untyped", "Campaign-test"],
            received_without_scopes,
        )

    def test_a_campaign_is_returned_once_even_when_a_filter_joins_a_to_many_relation(self):
        """What keeps the rows unique is the GROUP BY of the queryset's aggregate annotation, not a
        `.distinct()`. `campaign_types`, `rounds__started_at` and `scopes` all join a to-many
        relation, so a campaign matching several rows would otherwise be listed several times."""
        self.client.force_authenticate(self.user)
        self.campaign.campaign_types.set([self.polio_type, self.measles_type])
        CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[2][0])

        received_on_both_types = self.get_obr_names({"campaign_types": f"{self.polio_type.pk},{self.measles_type.pk}"})
        # Matches all three rounds of the fixture campaign.
        received_on_the_round_dates = self.get_obr_names({"rounds__started_at__gte": "2020-01-01"})
        # The fixture scope plus the one just added.
        received_on_the_scopes = self.get_obr_names({"has_scopes": "true"})

        self.assertEqual(["Campaign-1", "Campaign-measles"], received_on_both_types)
        self.assertEqual(["Campaign-1"], received_on_the_round_dates)
        self.assertEqual(["Campaign-1"], received_on_the_scopes)

    def test_search_filter(self):
        self.client.force_authenticate(self.user)

        received = self.get_obr_names({"search": "Campaign-untyped"})

        self.assertEqual(["Campaign-untyped"], received)

    def test_deleted_campaigns_are_excluded_by_default(self):
        """DeletionFilterBackend only defaults to "active" on the list action, so the action does it."""
        self.client.force_authenticate(self.user)

        received_by_default = self.get_obr_names()
        received_all = self.get_obr_names({"deletion_status": "all"})
        received_deleted_only = self.get_obr_names({"deletion_status": "deleted"})

        self.assertNotIn(self.deleted_campaign.obr_name, received_by_default)
        self.assertIn(self.deleted_campaign.obr_name, received_all)
        self.assertEqual(["Campaign-deleted"], received_deleted_only)

    def test_campaigns_are_ordered_by_their_first_round_start_date(self):
        """The select inputs show the campaign that started most recently first. `Campaign-1` is
        the fixture campaign, whose first round starts on 2021-01-01."""
        self.client.force_authenticate(self.user)
        self.create_campaign_starting_on("Campaign-oldest", datetime.date(2020, 1, 1))
        self.create_campaign_starting_on("Campaign-newest", datetime.date(2030, 1, 1))

        received = self.get_obr_names()

        expected = [
            "Campaign-newest",
            "Campaign-1",
            "Campaign-oldest",
            # No round, so no date to sort on: last, and tied on `obr_name` between them.
            "Campaign-measles",
            "Campaign-test",
            "Campaign-untyped",
        ]
        self.assertEqual(expected, received)

    def test_ordering_on_the_first_round_start_date_can_be_reversed(self):
        self.client.force_authenticate(self.user)
        self.create_campaign_starting_on("Campaign-oldest", datetime.date(2020, 1, 1))
        self.create_campaign_starting_on("Campaign-newest", datetime.date(2030, 1, 1))

        received = self.get_obr_names({"order": "first_round_started_at"})

        # Only the campaigns with a round: `order` replaces the queryset ordering, tiebreaker
        # included, so the ones sharing a NULL date have no defined order between them.
        expected_dated_campaigns = ["Campaign-oldest", "Campaign-1", "Campaign-newest"]
        self.assertEqual(expected_dated_campaigns, received[:3])

    def test_ordering_on_obr_name(self):
        """The ordering query param is `order` (REST_FRAMEWORK["ORDERING_PARAM"] in hat/settings.py)."""
        self.client.force_authenticate(self.user)

        received_ascending = self.get_obr_names({"order": "obr_name"})
        received_descending = self.get_obr_names({"order": "-obr_name"})

        expected_ascending = ["Campaign-1", "Campaign-measles", "Campaign-test", "Campaign-untyped"]
        self.assertEqual(expected_ascending, received_ascending)
        self.assertEqual(list(reversed(expected_ascending)), received_descending)

    def test_ordering_on_a_list_only_annotation_does_not_break(self):
        """`last_round_started_at` exists only as an annotation of the list queryset, and
        `OrderingFilter` silently drops an `order` term that is not whitelisted."""
        self.client.force_authenticate(self.user)

        response = self.client.get(BASE_URL, {"order": "last_round_started_at"})

        self.assertJSONResponse(response, status.HTTP_200_OK)

    def test_query_count_does_not_grow_with_the_number_of_campaigns(self):
        self.client.force_authenticate(self.user)

        with CaptureQueriesContext(connection) as before:
            response = self.client.get(BASE_URL)
            self.assertJSONResponse(response, status.HTTP_200_OK)

        for index in range(2, 7):
            self.create_campaign(
                obr_name=f"Campaign-{index}",
                account=self.account,
                source_version=self.source_version,
                country_ou_type=self.country_type,
                district_ou_type=self.district_type,
                country_name=f"Country-{index}",
                district_name=f"District-{index}",
            )

        with CaptureQueriesContext(connection) as after:
            received = self.get_payload()

        self.assertEqual(9, len(received))
        self.assertEqual(
            len(before.captured_queries),
            len(after.captured_queries),
            "The dropdown endpoint has an N+1:\n" + "\n".join(query["sql"] for query in after.captured_queries),
        )
        # One per prefetch (rounds, campaign types, campaign scopes, round scopes, sub-activities,
        # sub-activity scopes) plus the campaigns themselves, auth and the org unit restriction.
        self.assertLessEqual(len(after.captured_queries), 14)
