import datetime

import time_machine

from iaso import models as m
from iaso.test import APITestCase
from plugins.polio.models import Campaign, CampaignScope, CampaignType, Round


TODAY = datetime.datetime(2024, 10, 21, 11, 0, 0, 0, tzinfo=datetime.timezone.utc)


@time_machine.travel(TODAY, tick=False)
class CampaignCreateAllRoundsScopesCsvViewTestCase(APITestCase):
    """
    Test CampaignViewSet.create_all_rounds_scopes_csv.
    """

    @classmethod
    def setUpTestData(cls):
        cls.data_source = m.DataSource.objects.create(name="Data Source")
        cls.source_version = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)
        cls.account = m.Account.objects.create(name="Account", default_version=cls.source_version)
        cls.user = cls.create_user_with_profile(
            email="john@polio.org",
            username="john",
            first_name="John",
            last_name="Doe",
            account=cls.account,
        )

        cls.org_unit_a = m.OrgUnit.objects.create(
            name="A",
            org_unit_type=m.OrgUnitType.objects.create(category="COUNTRY"),
            validation_status=m.OrgUnit.VALIDATION_VALID,
            version=cls.source_version,
        )
        cls.org_unit_b = m.OrgUnit.objects.create(
            name="B",
            org_unit_type=m.OrgUnitType.objects.create(category="COUNTRY"),
            validation_status=m.OrgUnit.VALIDATION_VALID,
            version=cls.source_version,
            parent=cls.org_unit_a,
        )
        cls.org_unit_c = m.OrgUnit.objects.create(
            name="C",
            org_unit_type=m.OrgUnitType.objects.create(category="COUNTRY"),
            validation_status=m.OrgUnit.VALIDATION_VALID,
            version=cls.source_version,
            parent=cls.org_unit_b,
        )

        cls.group = m.Group.objects.create(name="Group", source_version=cls.source_version)
        cls.group.org_units.add(cls.org_unit_c)

        cls.campaign = Campaign.objects.create(obr_name="Campaign OBR name", account=cls.account)
        cls.round = Round.objects.create(number=1, campaign=cls.campaign, started_at=TODAY.date())
        cls.campaign_scope = CampaignScope.objects.create(campaign=cls.campaign, group=cls.group)

    def test_get_create_all_rounds_scopes_csv_ok(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(
            "/api/polio/campaigns/create_all_rounds_scopes_csv/?roundStartFrom=01-10-2024&roundStartTo=31-10-2024"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get("Content-Disposition"),
            "attachment; filename=all-rounds-scopes--start-from-01-10-2024--start-to-31-10-2024.csv",
        )

        response_csv = response.getvalue().decode("utf-8")
        expected_csv = (
            "ID,Admin 2,Admin 1,Admin 0,OBR Name,Round Number,Start date,Vaccine\r\n"
            f"{self.org_unit_c.id},C,B,A,Campaign OBR name,R1,2024-10-21,\r\n"
        )
        self.assertEqual(response_csv, expected_csv)

    def test_test_get_create_all_rounds_scopes_csv_should_exlude_test_campaigns(self):
        self.round.campaign.is_test = True
        self.round.campaign.save()

        self.client.force_authenticate(self.user)
        response = self.client.get(
            "/api/polio/campaigns/create_all_rounds_scopes_csv/?roundStartFrom=01-10-2024&roundStartTo=31-10-2024"
        )

        self.assertEqual(response.status_code, 200)
        response_csv = response.getvalue().decode("utf-8")
        expected_csv = "ID,Admin 2,Admin 1,Admin 0,OBR Name,Round Number,Start date,Vaccine\r\n"
        self.assertEqual(response_csv, expected_csv)

    def test_test_get_create_all_rounds_scopes_csv_should_exlude_rounds_without_campaigns(self):
        self.round.campaign = None
        self.round.save()

        self.client.force_authenticate(self.user)
        response = self.client.get(
            "/api/polio/campaigns/create_all_rounds_scopes_csv/?roundStartFrom=01-10-2024&roundStartTo=31-10-2024"
        )

        self.assertEqual(response.status_code, 200)
        response_csv = response.getvalue().decode("utf-8")
        expected_csv = "ID,Admin 2,Admin 1,Admin 0,OBR Name,Round Number,Start date,Vaccine\r\n"
        self.assertEqual(response_csv, expected_csv)


@time_machine.travel(TODAY, tick=False)
class CampaignCreateAllRoundsScopesCsvCampaignTypeTestCase(APITestCase):
    """
    Test that the calendar's campaign type filter reaches the rounds CSV export.
    """

    @classmethod
    def setUpTestData(cls):
        cls.data_source = m.DataSource.objects.create(name="Data Source")
        cls.source_version = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)
        cls.account = m.Account.objects.create(name="Account", default_version=cls.source_version)
        cls.user = cls.create_user_with_profile(username="john", account=cls.account)

        country_type = m.OrgUnitType.objects.create(category="COUNTRY")
        cls.country_a = m.OrgUnit.objects.create(
            name="A",
            org_unit_type=country_type,
            validation_status=m.OrgUnit.VALIDATION_VALID,
            version=cls.source_version,
        )
        cls.country_b = m.OrgUnit.objects.create(
            name="B",
            org_unit_type=country_type,
            validation_status=m.OrgUnit.VALIDATION_VALID,
            version=cls.source_version,
        )
        cls.polio, _ = CampaignType.objects.get_or_create(name=CampaignType.POLIO)
        cls.measles, _ = CampaignType.objects.get_or_create(name=CampaignType.MEASLES)

        cls.polio_campaign = cls._scoped_campaign("Polio OBR name", [cls.polio])
        cls.measles_campaign = cls._scoped_campaign("Measles OBR name", [cls.measles])

    @classmethod
    def _scoped_campaign(cls, obr_name, campaign_types):
        """A campaign in country A with one round today, scoped to country A.

        Each campaign gets its own group: CampaignScope.group is a OneToOneField.
        """
        group = m.Group.objects.create(name=f"{obr_name} scope", source_version=cls.source_version)
        group.org_units.add(cls.country_a)
        campaign = Campaign.objects.create(obr_name=obr_name, account=cls.account, country=cls.country_a)
        campaign.campaign_types.set(campaign_types)
        Round.objects.create(number=1, campaign=campaign, started_at=TODAY.date())
        CampaignScope.objects.create(campaign=campaign, group=group)
        return campaign

    def _obr_names(self, query=""):
        """OBR Name of every CSV row, in order, duplicates kept."""
        self.client.force_authenticate(self.user)
        response = self.client.get(
            "/api/polio/campaigns/create_all_rounds_scopes_csv/?roundStartFrom=01-10-2024&roundStartTo=31-10-2024"
            + query
        )
        self.assertEqual(response.status_code, 200)
        lines = response.getvalue().decode("utf-8").splitlines()
        self.assertEqual(lines[0], "ID,Admin 2,Admin 1,Admin 0,OBR Name,Round Number,Start date,Vaccine")
        return [line.split(",")[4] for line in lines[1:]]

    def test_no_type_filter_exports_every_type(self):
        self.assertCountEqual(self._obr_names(), ["Polio OBR name", "Measles OBR name"])

    def test_campaign_type_slug_as_sent_by_the_calendar(self):
        self.assertEqual(self._obr_names("&campaignType=polio"), ["Polio OBR name"])

    def test_campaign_type_id(self):
        self.assertEqual(self._obr_names(f"&campaignType={self.polio.id}"), ["Polio OBR name"])

    def test_campaign_types_spelling_of_the_campaigns_list(self):
        self.assertEqual(self._obr_names("&campaign_types=measles"), ["Measles OBR name"])

    def test_several_types(self):
        self.assertCountEqual(self._obr_names("&campaignType=polio,measles"), ["Polio OBR name", "Measles OBR name"])

    def test_campaign_with_two_requested_types_is_listed_once(self):
        self._scoped_campaign("Integrated OBR name", [self.polio, self.measles])

        # assertCountEqual counts duplicates: a join without a subquery/distinct
        # would return "Integrated OBR name" twice.
        self.assertCountEqual(
            self._obr_names("&campaignType=polio,measles"),
            ["Polio OBR name", "Measles OBR name", "Integrated OBR name"],
        )

    def test_unknown_type_exports_nothing(self):
        self.assertEqual(self._obr_names("&campaignType=no_such_type"), [])

    def test_test_campaigns_stay_excluded_under_a_type_filter(self):
        self.polio_campaign.is_test = True
        self.polio_campaign.save()

        self.assertEqual(self._obr_names("&campaignType=polio"), [])

    def test_type_filter_combines_with_countries(self):
        self.assertEqual(self._obr_names(f"&campaignType=measles&countries={self.country_a.id}"), ["Measles OBR name"])
        self.assertEqual(self._obr_names(f"&campaignType=measles&countries={self.country_b.id}"), [])
