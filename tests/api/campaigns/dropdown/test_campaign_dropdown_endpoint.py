from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from iaso import models as m
from iaso.models import Account
from iaso.test import APITestCase
from plugins.polio.models import (
    VACCINES,
    Campaign,
    CampaignScope,
    CampaignType,
    RoundScope,
    SubActivity,
    SubActivityScope,
)
from plugins.polio.tests.api.test import PolioTestCaseMixin


BASE_URL = "/api/polio/campaigns/dropdown/"


class CampaignDropdownEndpointTestCase(APITestCase, PolioTestCaseMixin):
    """The lightweight endpoint feeding campaign select inputs (Form A, Earmarked...)."""

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

        cls.campaign, cls.round_1, cls.round_2, cls.round_3, cls.country, cls.district = cls.create_campaign(
            obr_name="Campaign-1",
            account=cls.account,
            source_version=cls.source_version,
            country_ou_type=cls.country_type,
            district_ou_type=cls.district_type,
            country_name="Country-1",
            district_name="District-1",
        )

        # Another account's campaign: must never show up.
        cls.other_account = Account.objects.create(name="other", default_version=cls.source_version)
        cls.other_campaign = Campaign.objects.create(obr_name="Campaign-other-account", account=cls.other_account)

    def test_requires_authentication(self):
        """Stricter than the list endpoint, which allows anonymous reads for the embedded calendar."""
        response = self.client.get(BASE_URL)
        self.assertIn(response.status_code, [HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN])

    def test_anonymous_cannot_bypass_with_account_id(self):
        """The list endpoint honours `account_id` for anonymous callers; the dropdown must not."""
        response = self.client.get(f"{BASE_URL}?account_id={self.account.pk}")
        self.assertIn(response.status_code, [401, 403])

    def test_write_methods_are_not_exposed(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(BASE_URL, data={}, format="json").status_code, HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(BASE_URL).status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_of_another_account_only_sees_its_own_campaigns(self):
        other_user = self.create_user_with_profile(username="user-2", account=self.other_account)
        self.client.force_authenticate(other_user)

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-other-account"])

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

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-2"])

    def test_payload_is_minimal(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(BASE_URL)
        data = self.assertJSONResponse(response, HTTP_200_OK)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        campaign_data = data[0]
        self.assertEqual(
            sorted(campaign_data.keys()),
            [
                "campaign_types",
                "created_at",
                "id",
                "obr_name",
                "rounds",
                "separate_scopes_per_round",
                "vaccines",
            ],
        )
        self.assertEqual(campaign_data["id"], str(self.campaign.id))
        self.assertEqual(campaign_data["obr_name"], "Campaign-1")

        rounds = campaign_data["rounds"]
        self.assertEqual(len(rounds), 3)
        self.assertEqual(
            sorted(rounds[0].keys()),
            ["ended_at", "has_scope", "id", "number", "on_hold", "started_at", "vaccines"],
        )
        self.assertEqual([r["started_at"] for r in rounds], sorted(r["started_at"] for r in rounds))
        self.assertEqual([r["number"] for r in rounds], [1, 2, 3])
        self.assertEqual(rounds[0]["id"], self.round_1.id)

    def test_other_account_campaigns_are_not_visible(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(BASE_URL)
        data = self.assertJSONResponse(response, HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-1"])

    def test_rounds_inherit_the_campaign_vaccines_when_scopes_are_not_split(self):
        self.client.force_authenticate(self.user)
        self.assertFalse(self.campaign.separate_scopes_per_round)

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)

        self.assertEqual(data[0]["vaccines"], [VACCINES[0][0]])
        for round_data in data[0]["rounds"]:
            self.assertEqual(round_data["vaccines"], [VACCINES[0][0]])
            self.assertFalse(round_data["has_scope"])

    def test_rounds_use_their_own_scopes_when_scopes_are_split(self):
        self.client.force_authenticate(self.user)
        self.campaign.separate_scopes_per_round = True
        self.campaign.save()
        round_scope = RoundScope.objects.create(round=self.round_2, vaccine=VACCINES[2][0])
        round_scope.group.org_units.add(self.district)

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)
        rounds_by_number = {round_data["number"]: round_data for round_data in data[0]["rounds"]}

        self.assertEqual(rounds_by_number[2]["vaccines"], [VACCINES[2][0]])
        self.assertTrue(rounds_by_number[2]["has_scope"])
        self.assertEqual(rounds_by_number[1]["vaccines"], [])
        self.assertFalse(rounds_by_number[1]["has_scope"])

    def test_scopes_without_org_units_name_no_round_vaccine(self):
        self.client.force_authenticate(self.user)
        self.campaign.scopes.all().delete()
        CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[1][0])

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)

        self.assertEqual(data[0]["vaccines"], [])
        self.assertEqual([r["vaccines"] for r in data[0]["rounds"]], [[], [], []])

    def test_combined_vaccines_are_split(self):
        self.client.force_authenticate(self.user)
        self.campaign.scopes.all().delete()
        combined_scope = CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[3][0])
        combined_scope.group.org_units.add(self.district)

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)

        self.assertEqual(data[0]["vaccines"], sorted([VACCINES[1][0], VACCINES[2][0]]))

    def test_vaccines_match_the_model_properties(self):
        self.client.force_authenticate(self.user)

        for separate_scopes_per_round in [False, True]:
            with self.subTest(separate_scopes_per_round=separate_scopes_per_round):
                self.campaign.separate_scopes_per_round = separate_scopes_per_round
                self.campaign.save()
                # One pass per scope mode, so clear everything first: `RoundScope` is unique
                # per (round, vaccine) and leftovers from the previous pass would collide.
                self.campaign.scopes.all().delete()
                RoundScope.objects.filter(round__campaign=self.campaign).delete()
                # Cascades to the sub-activities' own scopes.
                SubActivity.objects.filter(round__campaign=self.campaign).delete()

                campaign_scope = CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[0][0])
                campaign_scope.group.org_units.add(self.district)
                combined_scope = CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[3][0])
                combined_scope.group.org_units.add(self.district)
                CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[2][0])

                round_scope = RoundScope.objects.create(round=self.round_2, vaccine=VACCINES[1][0])
                round_scope.group.org_units.add(self.district)
                RoundScope.objects.create(round=self.round_3, vaccine=VACCINES[2][0])

                sub_activity = SubActivity.objects.create(round=self.round_1, name="Mop up")
                sub_activity_scope = SubActivityScope.objects.create(subactivity=sub_activity, vaccine=VACCINES[2][0])
                sub_activity_scope.group.org_units.add(self.district)

                data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)
                campaign_data = next(c for c in data if c["obr_name"] == self.campaign.obr_name)

                campaign = Campaign.objects.get(pk=self.campaign.pk)
                self.assertEqual(campaign_data["vaccines"], campaign.single_vaccines_extended_list)
                self.assertTrue(campaign_data["vaccines"])

                rounds_by_number = {r["number"]: r for r in campaign_data["rounds"]}
                for round in campaign.rounds.all():
                    with self.subTest(round=round.number):
                        self.assertEqual(
                            rounds_by_number[round.number]["vaccines"],
                            round.single_vaccine_list_extended,
                        )

    def test_has_scopes_filter(self):
        self.client.force_authenticate(self.user)
        CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[1][0])
        Campaign.objects.create(obr_name="Campaign-without-scope", account=self.account)
        per_round = Campaign.objects.create(
            obr_name="Campaign-per-round-scopes", account=self.account, separate_scopes_per_round=True
        )

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?has_scopes=true"), HTTP_200_OK)
        self.assertCountEqual([c["obr_name"] for c in data], ["Campaign-1", per_round.obr_name])

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?has_scopes=false"), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-without-scope"])

    def test_has_scopes_filter_does_not_duplicate_campaigns(self):
        self.client.force_authenticate(self.user)
        CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[1][0])
        CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[2][0])

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?has_scopes=true"), HTTP_200_OK)

        self.assertEqual([c["obr_name"] for c in data], ["Campaign-1"])

    def test_country_name_filter(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(f"{BASE_URL}?country__name=Country-1")
        self.assertEqual(len(self.assertJSONResponse(response, HTTP_200_OK)), 1)

        response = self.client.get(f"{BASE_URL}?country__name=Country-2")
        self.assertEqual(len(self.assertJSONResponse(response, HTTP_200_OK)), 0)

    def test_show_test_filter(self):
        """Same semantics as the list endpoint: `filter_show_test` only runs when the param is sent."""
        self.client.force_authenticate(self.user)
        test_campaign = Campaign.objects.create(obr_name="Campaign-test", account=self.account, is_test=True)

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?show_test=false"), HTTP_200_OK)
        self.assertNotIn(test_campaign.obr_name, [c["obr_name"] for c in data])

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?show_test=true"), HTTP_200_OK)
        self.assertIn(test_campaign.obr_name, [c["obr_name"] for c in data])

    def test_campaign_types_are_serialized(self):
        """Rendered by the integrated campaigns rows, which is why they travel with the options."""
        self.client.force_authenticate(self.user)
        campaign_type = CampaignType.objects.create(name="Type-1")
        self.campaign.campaign_types.set([campaign_type])

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)
        campaign_types = data[0]["campaign_types"]
        self.assertEqual(len(campaign_types), 1)
        self.assertEqual(sorted(campaign_types[0].keys()), ["id", "name"])
        self.assertEqual(campaign_types[0]["id"], campaign_type.pk)
        self.assertEqual(campaign_types[0]["name"], "Type-1")

    def test_campaign_types_filter(self):
        self.client.force_authenticate(self.user)
        campaign_type = CampaignType.objects.create(name="Type-1")
        self.campaign.campaign_types.set([campaign_type])
        Campaign.objects.create(obr_name="Campaign-untyped", account=self.account)

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?campaign_types={campaign_type.pk}"), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-1"])

    def test_campaign_types_of_another_accounts_campaign_are_not_returned(self):
        """CampaignType rows are global, so the only thing scoping them is the campaign they hang off."""
        self.client.force_authenticate(self.user)
        own_type = CampaignType.objects.create(name="Type-own")
        other_type = CampaignType.objects.create(name="Type-other-account")
        self.campaign.campaign_types.set([own_type])
        self.other_campaign.campaign_types.set([other_type])

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)
        returned_types = [campaign_type["name"] for campaign in data for campaign_type in campaign["campaign_types"]]
        self.assertEqual(returned_types, ["Type-own"])

    def test_filtering_on_another_accounts_campaign_type_returns_nothing(self):
        """A global type id must not be a way to read across accounts."""
        self.client.force_authenticate(self.user)
        other_type = CampaignType.objects.create(name="Type-other-account")
        self.other_campaign.campaign_types.set([other_type])

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?campaign_types={other_type.pk}"), HTTP_200_OK)
        self.assertEqual(data, [])

    def test_search_filter(self):
        self.client.force_authenticate(self.user)
        Campaign.objects.create(obr_name="Campaign-unrelated", account=self.account)

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?search=Campaign-1"), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-1"])

    def test_deleted_campaigns_are_excluded_by_default(self):
        """DeletionFilterBackend only defaults to "active" on the list action, so the action does it."""
        self.client.force_authenticate(self.user)
        deleted = Campaign.objects.create(obr_name="Campaign-deleted", account=self.account, deleted_at=timezone.now())

        data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)
        self.assertNotIn(deleted.obr_name, [c["obr_name"] for c in data])

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?deletion_status=all"), HTTP_200_OK)
        self.assertIn(deleted.obr_name, [c["obr_name"] for c in data])

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?deletion_status=deleted"), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-deleted"])

    def test_ordering_on_obr_name(self):
        """The ordering query param is `order` (REST_FRAMEWORK["ORDERING_PARAM"] in hat/settings.py)."""
        self.client.force_authenticate(self.user)
        # Starts with an "A" so the expected order holds whatever the database collation does with digits.
        Campaign.objects.create(obr_name="Another-campaign", account=self.account)

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?order=obr_name"), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Another-campaign", "Campaign-1"])

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?order=-obr_name"), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-1", "Another-campaign"])

    def test_ordering_on_a_list_only_annotation_does_not_break(self):
        """`last_round_started_at` exists only as an annotation of the list queryset."""
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{BASE_URL}?order=last_round_started_at")
        self.assertJSONResponse(response, HTTP_200_OK)

    def test_query_count_does_not_grow_with_the_number_of_campaigns(self):
        self.client.force_authenticate(self.user)

        with CaptureQueriesContext(connection) as one_campaign:
            self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)

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

        with CaptureQueriesContext(connection) as six_campaigns:
            data = self.assertJSONResponse(self.client.get(BASE_URL), HTTP_200_OK)

        self.assertEqual(len(data), 6)
        self.assertEqual(
            len(six_campaigns.captured_queries),
            len(one_campaign.captured_queries),
            "The dropdown endpoint has an N+1:\n" + "\n".join(q["sql"] for q in six_campaigns.captured_queries),
        )
        # One per prefetch (rounds, campaign types, campaign scopes, round scopes, sub-activities,
        # sub-activity scopes) plus the campaigns themselves, auth and the org unit restriction.
        self.assertLessEqual(len(six_campaigns.captured_queries), 14)
