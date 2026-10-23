from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.status import HTTP_200_OK

from iaso import models as m
from iaso.models import Account
from iaso.test import APITestCase
from plugins.polio.models import Campaign
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
        response = self.client.get(BASE_URL)
        self.assertIn(response.status_code, [401, 403])

    def test_payload_is_minimal(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(BASE_URL)
        data = self.assertJSONResponse(response, HTTP_200_OK)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        campaign_data = data[0]
        self.assertEqual(sorted(campaign_data.keys()), ["created_at", "id", "obr_name", "rounds"])
        self.assertEqual(campaign_data["id"], str(self.campaign.id))
        self.assertEqual(campaign_data["obr_name"], "Campaign-1")

        rounds = campaign_data["rounds"]
        self.assertEqual(len(rounds), 3)
        self.assertEqual(sorted(rounds[0].keys()), ["id", "number", "on_hold"])
        # Ordered by number, which is what the round select renders.
        self.assertEqual([r["number"] for r in rounds], [1, 2, 3])
        self.assertEqual(rounds[0]["id"], self.round_1.id)

    def test_other_account_campaigns_are_not_visible(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(BASE_URL)
        data = self.assertJSONResponse(response, HTTP_200_OK)
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

    def test_search_filter(self):
        self.client.force_authenticate(self.user)
        Campaign.objects.create(obr_name="Campaign-unrelated", account=self.account)

        data = self.assertJSONResponse(self.client.get(f"{BASE_URL}?search=Campaign-1"), HTTP_200_OK)
        self.assertEqual([c["obr_name"] for c in data], ["Campaign-1"])

    def test_deleted_campaigns_are_excluded_by_default(self):
        """DeletionFilterBackend only defaults to "active" on the list action, so the action does it."""
        self.client.force_authenticate(self.user)
        deleted = Campaign.objects.create(
            obr_name="Campaign-deleted", account=self.account, deleted_at=timezone.now()
        )

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
        # No prefetch chain to drift here, so an absolute ceiling is safe to pin.
        self.assertLessEqual(len(six_campaigns.captured_queries), 10)
