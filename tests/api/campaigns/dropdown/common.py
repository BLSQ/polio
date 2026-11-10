import datetime

from django.utils import timezone
from rest_framework import status

from iaso import models as m
from iaso.models import Account
from iaso.test import APITestCase
from plugins.polio.models import Campaign, CampaignType, Round
from plugins.polio.tests.api.test import PolioTestCaseMixin


BASE_URL = "/api/polio/campaigns/dropdown/"


class CampaignDropdownAPIBase(APITestCase, PolioTestCaseMixin):
    """Enough campaigns to exercise the filters: one with rounds and a scope, one with another
    type, one with no type, a test one, a deleted one, and one on another account.

    Shared by the serializer tests (what the payload holds) and the view tests (who sees what,
    which filters apply, in what order).
    """

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

        # The usual types are created by a data migration, and `name` is unique.
        cls.polio_type = CampaignType.objects.get(name=CampaignType.POLIO)
        cls.measles_type = CampaignType.objects.get(name=CampaignType.MEASLES)

        # The fixture also creates a campaign-level scope for VACCINES[0][0] whose group holds the
        # district, so a test that wants another vaccine has to clear it first.
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

    def get_payload(self, query_params=None):
        response = self.client.get(BASE_URL, query_params or {})
        return self.assertJSONResponse(response, status.HTTP_200_OK)

    def get_obr_names(self, query_params=None):
        return [campaign["obr_name"] for campaign in self.get_payload(query_params)]

    def get_campaign_payload(self, campaign=None):
        """One campaign's options, since the global setup holds several."""
        campaign = campaign or self.campaign
        received = self.get_payload({"search": campaign.obr_name})
        return next(option for option in received if option["obr_name"] == campaign.obr_name)

    def create_campaign_starting_on(self, obr_name, started_at: datetime.date):
        """`create_campaign` hardcodes its round dates, so the ordering needs its own campaigns."""
        campaign = Campaign.objects.create(obr_name=obr_name, account=self.account)
        Round.objects.create(campaign=campaign, number=1, started_at=started_at)
        return campaign
