from django.core.management import call_command

from iaso import models as m
from iaso.models import Account
from iaso.test import TestCase
from plugins.polio import models as pm
from plugins.polio.tests.api.test import PolioTestCaseMixin


class AddStockHistoryCommandTestCase(TestCase, PolioTestCaseMixin):
    @classmethod
    def setUpTestData(cls):
        cls.data_source = m.DataSource.objects.create(name="Default source")
        cls.source_version = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)
        cls.account = Account.objects.create(name="polio", default_version=cls.source_version)
        # `category="COUNTRY"` matters: Campaign.save() recomputes `country` from the COUNTRY-category
        # ancestor, and the command looks the stock up by country.
        cls.country_type = m.OrgUnitType.objects.create(name="COUNTRY", short_name="country", category="COUNTRY")
        cls.district_type = m.OrgUnitType.objects.create(name="DISTRICT", short_name="district")

    def campaign_with_scope_and_stocks(self, obr_name, vaccine, stock_vaccines, vrf_vaccine):
        campaign, round_1, _round_2, _round_3, country, _district = self.create_campaign(
            obr_name=obr_name,
            account=self.account,
            source_version=self.source_version,
            country_ou_type=self.country_type,
            district_ou_type=self.district_type,
            country_name=f"{obr_name}-country",
            district_name=f"{obr_name}-district",
            vaccine=vaccine,
        )
        vaccine_request_form = pm.VaccineRequestForm.objects.create(
            campaign=campaign,
            vaccine_type=vrf_vaccine,
            quantities_ordered_in_doses=500,
        )
        vaccine_request_form.rounds.set([round_1])
        for stock_vaccine in stock_vaccines:
            pm.VaccineStock.objects.get_or_create(country=country, vaccine=stock_vaccine, account=self.account)
        return round_1

    def archived_vaccines(self, round):
        return sorted(
            pm.VaccineStockHistory.objects.filter(round=round).values_list("vaccine_stock__vaccine", flat=True)
        )

    def test_combined_fipv_scope_is_archived_against_ipv_and_bopv(self):
        round_1 = self.campaign_with_scope_and_stocks(
            "CAMPAIGN_FIPV_BOPV", "fIPV & bOPV", ["IPV", "bOPV"], vrf_vaccine="IPV"
        )

        call_command("add_stock_history")

        expected_vaccines = sorted(["IPV", "bOPV"])
        received_vaccines = self.archived_vaccines(round_1)
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_fipv_scope_is_archived_under_ipv(self):
        round_1 = self.campaign_with_scope_and_stocks("CAMPAIGN_FIPV", "fIPV", ["IPV"], vrf_vaccine="IPV")

        call_command("add_stock_history")

        expected_vaccines = ["IPV"]
        received_vaccines = self.archived_vaccines(round_1)
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_legacy_combined_scope_still_archives_both_vaccines(self):
        round_1 = self.campaign_with_scope_and_stocks(
            "CAMPAIGN_NOPV2_BOPV", "nOPV2 & bOPV", ["nOPV2", "bOPV"], vrf_vaccine="nOPV2"
        )

        call_command("add_stock_history")

        expected_vaccines = sorted(["nOPV2", "bOPV"])
        received_vaccines = self.archived_vaccines(round_1)
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_no_fipv_stock_is_ever_looked_up(self):
        round_1 = self.campaign_with_scope_and_stocks(
            "CAMPAIGN_FIPV_NO_STOCK", "fIPV & nOPV2", ["IPV", "nOPV2"], vrf_vaccine="IPV"
        )

        call_command("add_stock_history")

        self.assertNotIn("fIPV", self.archived_vaccines(round_1))
        self.assertFalse(pm.VaccineStock.objects.filter(vaccine="fIPV").exists())

    def test_running_twice_adds_no_duplicate_history(self):
        round_1 = self.campaign_with_scope_and_stocks(
            "CAMPAIGN_FIPV_TWICE", "fIPV & bOPV", ["IPV", "bOPV"], vrf_vaccine="IPV"
        )

        call_command("add_stock_history")
        call_command("add_stock_history")

        expected_vaccines = sorted(["IPV", "bOPV"])
        received_vaccines = self.archived_vaccines(round_1)
        self.assertEqual(expected_vaccines, received_vaccines)
