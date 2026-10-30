import datetime

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status

from iaso import models as m
from iaso.models import Account
from iaso.test import APITestCase, SwaggerTestCaseMixin
from plugins.polio.models import Campaign, CampaignType, Round
from plugins.polio.tests.api.test import PolioTestCaseMixin


BASE_URL = "/api/polio/campaigns/dropdown/"


class CampaignDropdownEndpointTestCase(SwaggerTestCaseMixin, APITestCase, PolioTestCaseMixin):
    """The lightweight endpoint feeding campaign select inputs (Form A and Earmarked)."""

    @classmethod
    def setUpTestData(cls):
        cls.data_source = m.DataSource.objects.create(name="Default source")
        cls.source_version = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)
        cls.account = Account.objects.create(name="polio", default_version=cls.source_version)
        cls.user = cls.create_user_with_profile(username="user-1", account=cls.account)

        # `category="COUNTRY"` matters: Campaign.save() recomputes `country` from the COUNTRY-category
        # ancestor of initial_org_unit, so without it the campaign ends up with country=None.
        cls.country_type = m.OrgUnitType.objects.create(name="COUNTRY", short_name="country", category="COUNTRY")
        cls.district_type = m.OrgUnitType.objects.create(name="DISTRICT", short_name="district")

        # The usual types are created by a data migration, `name` is unique.
        cls.polio_type = CampaignType.objects.get(name=CampaignType.POLIO)
        cls.measles_type = CampaignType.objects.get(name=CampaignType.MEASLES)

        cls.campaign, cls.round_1, cls.round_2, cls.round_3, cls.country, cls.district = cls.create_campaign(
            obr_name="Campaign-1",
            account=cls.account,
            source_version=cls.source_version,
            country_ou_type=cls.country_type,
            district_ou_type=cls.district_type,
            country_name="Country-1",
            district_name="District-1",
        )
        cls.campaign.campaign_types.set([cls.polio_type])

        cls.measles_campaign = Campaign.objects.create(obr_name="Campaign-measles", account=cls.account)
        cls.measles_campaign.campaign_types.set([cls.measles_type])

        cls.untyped_campaign = Campaign.objects.create(obr_name="Campaign-untyped", account=cls.account)

        cls.test_campaign = Campaign.objects.create(obr_name="Campaign-test", account=cls.account, is_test=True)

        cls.deleted_campaign = Campaign.objects.create(
            obr_name="Campaign-deleted", account=cls.account, deleted_at=timezone.now()
        )

        # Another account's campaign: must never show up.
        cls.other_account = Account.objects.create(name="other", default_version=cls.source_version)
        cls.other_campaign = Campaign.objects.create(obr_name="Campaign-other-account", account=cls.other_account)
        cls.other_campaign.campaign_types.set([cls.polio_type])

    def get_obr_names(self, query_params=None):
        response = self.client.get(BASE_URL, query_params or {})
        data = self.assertJSONResponse(response, status.HTTP_200_OK)
        return [campaign["obr_name"] for campaign in data]

    def create_campaign_starting_on(self, obr_name, started_at):
        campaign = Campaign.objects.create(obr_name=obr_name, account=self.account)
        Round.objects.create(campaign=campaign, number=1, started_at=started_at)
        return campaign

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

    def test_payload_format(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(BASE_URL, {"search": self.campaign.obr_name})
        data = self.assertJSONResponse(response, status.HTTP_200_OK)

        self.assertResponseCompliantToSwagger(data, "CampaignDropdownOption", as_array=True)
        self.assertEqual(
            data,
            [
                {
                    "id": str(self.campaign.id),
                    "obr_name": "Campaign-1",
                    "campaign_types": [{"id": self.polio_type.pk, "name": "Polio"}],
                    "rounds": [
                        {
                            "id": self.round_1.id,
                            "number": self.round_1.number,
                            "on_hold": self.round_1.on_hold,
                            "started_at": self.round_1.started_at.isoformat(),
                        },
                        {
                            "id": self.round_2.id,
                            "number": self.round_2.number,
                            "on_hold": self.round_2.on_hold,
                            "started_at": self.round_2.started_at.isoformat(),
                        },
                        {
                            "id": self.round_3.id,
                            "number": self.round_3.number,
                            "on_hold": self.round_3.on_hold,
                            "started_at": self.round_3.started_at.isoformat(),
                        },
                    ],
                }
            ],
        )

    def test_campaigns_are_ordered_by_their_first_round_start_date(self):
        self.client.force_authenticate(self.user)
        self.create_campaign_starting_on("Campaign-oldest", datetime.date(2020, 1, 1))
        self.create_campaign_starting_on("Campaign-newest", datetime.date(2030, 1, 1))

        obr_names = self.get_obr_names()

        self.assertEqual(
            obr_names,
            [
                "Campaign-newest",
                "Campaign-1",
                "Campaign-oldest",
                # No round, so no date to sort on: last, and tied on `obr_name` between them.
                "Campaign-measles",
                "Campaign-test",
                "Campaign-untyped",
            ],
        )

    def test_ordering_on_the_first_round_start_date_can_be_reversed(self):
        self.client.force_authenticate(self.user)
        self.create_campaign_starting_on("Campaign-oldest", datetime.date(2020, 1, 1))
        self.create_campaign_starting_on("Campaign-newest", datetime.date(2030, 1, 1))

        obr_names = self.get_obr_names({"order": "first_round_started_at"})

        self.assertEqual(
            [name for name in obr_names if name in {"Campaign-oldest", "Campaign-1", "Campaign-newest"}],
            ["Campaign-oldest", "Campaign-1", "Campaign-newest"],
        )

    def test_ordering_on_obr_name(self):
        self.client.force_authenticate(self.user)

        ascending = self.get_obr_names({"order": "obr_name"})
        descending = self.get_obr_names({"order": "-obr_name"})

        self.assertEqual(ascending, ["Campaign-1", "Campaign-measles", "Campaign-test", "Campaign-untyped"])
        self.assertEqual(descending, ["Campaign-untyped", "Campaign-test", "Campaign-measles", "Campaign-1"])

    def test_user_of_another_account_only_sees_its_own_campaigns(self):
        other_user = self.create_user_with_profile(username="user-2", account=self.other_account)
        self.client.force_authenticate(other_user)

        obr_names = self.get_obr_names()

        self.assertEqual(obr_names, ["Campaign-other-account"])

    def test_user_restricted_to_org_units_only_sees_campaigns_in_their_hierarchy(self):
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

        obr_names = self.get_obr_names()

        self.assertEqual(obr_names, ["Campaign-2"])

    def test_other_account_campaigns_are_not_visible(self):
        self.client.force_authenticate(self.user)

        obr_names = self.get_obr_names()

        self.assertNotIn(self.other_campaign.obr_name, obr_names)

    def test_country_name_filter(self):
        self.client.force_authenticate(self.user)

        matching = self.get_obr_names({"country__name": "Country-1"})
        not_matching = self.get_obr_names({"country__name": "Country-unknown"})

        self.assertEqual(matching, ["Campaign-1"])
        self.assertEqual(not_matching, [])

    def test_country_id_filter(self):
        self.client.force_authenticate(self.user)

        obr_names = self.get_obr_names({"country__id__in": self.country.pk})

        self.assertEqual(obr_names, ["Campaign-1"])

    def test_show_test_filter(self):
        self.client.force_authenticate(self.user)

        without_test_campaigns = self.get_obr_names({"show_test": "false"})
        with_test_campaigns = self.get_obr_names({"show_test": "true"})

        self.assertNotIn(self.test_campaign.obr_name, without_test_campaigns)
        self.assertIn(self.test_campaign.obr_name, with_test_campaigns)

    def test_campaign_types_filter(self):
        self.client.force_authenticate(self.user)

        on_polio = self.get_obr_names({"campaign_types": self.polio_type.pk})
        on_measles = self.get_obr_names({"campaign_types": self.measles_type.pk})
        on_both = self.get_obr_names({"campaign_types": f"{self.polio_type.pk},{self.measles_type.pk}"})

        self.assertEqual(on_polio, ["Campaign-1"])
        self.assertEqual(on_measles, ["Campaign-measles"])
        self.assertEqual(on_both, ["Campaign-1", "Campaign-measles"])

    def test_a_campaign_is_returned_once_even_when_a_filter_joins_a_to_many_relation(self):
        self.client.force_authenticate(self.user)
        self.campaign.campaign_types.set([self.polio_type, self.measles_type])

        on_both_types = self.get_obr_names({"campaign_types": f"{self.polio_type.pk},{self.measles_type.pk}"})
        # Matches all three rounds of the fixture campaign.
        on_the_round_dates = self.get_obr_names({"rounds__started_at__gte": "2020-01-01"})

        self.assertEqual(on_both_types, ["Campaign-1", "Campaign-measles"])
        self.assertEqual(on_the_round_dates, ["Campaign-1"])

    def test_filtering_on_another_accounts_campaign_type_returns_nothing(self):
        """A global type id must not be a way to read across accounts."""
        self.client.force_authenticate(self.user)
        other_type = CampaignType.objects.create(name="Type-other-account")
        self.other_campaign.campaign_types.set([other_type])

        obr_names = self.get_obr_names({"campaign_types": other_type.pk})

        self.assertEqual(obr_names, [])

    def test_campaign_types_of_another_accounts_campaign_are_not_returned(self):
        """CampaignType rows are global, so the only thing scoping them is the campaign they hang off."""
        self.client.force_authenticate(self.user)
        other_type = CampaignType.objects.create(name="Type-other-account")
        self.other_campaign.campaign_types.set([other_type])

        response = self.client.get(BASE_URL)
        data = self.assertJSONResponse(response, status.HTTP_200_OK)

        returned_types = [campaign_type["name"] for campaign in data for campaign_type in campaign["campaign_types"]]
        self.assertEqual(returned_types, ["Polio", "Measles"])

    def test_search_filter(self):
        self.client.force_authenticate(self.user)

        obr_names = self.get_obr_names({"search": "Campaign-untyped"})

        self.assertEqual(obr_names, ["Campaign-untyped"])

    def test_deleted_campaigns_are_excluded_by_default(self):
        self.client.force_authenticate(self.user)

        by_default = self.get_obr_names()
        all_campaigns = self.get_obr_names({"deletion_status": "all"})
        deleted_only = self.get_obr_names({"deletion_status": "deleted"})

        self.assertNotIn(self.deleted_campaign.obr_name, by_default)
        self.assertIn(self.deleted_campaign.obr_name, all_campaigns)
        self.assertEqual(deleted_only, ["Campaign-deleted"])

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
            response = self.client.get(BASE_URL)
            data = self.assertJSONResponse(response, status.HTTP_200_OK)

        self.assertEqual(len(data), 9)
        self.assertEqual(
            len(after.captured_queries),
            len(before.captured_queries),
            "The dropdown endpoint has an N+1:\n" + "\n".join(query["sql"] for query in after.captured_queries),
        )
        self.assertLessEqual(len(after.captured_queries), 10)
