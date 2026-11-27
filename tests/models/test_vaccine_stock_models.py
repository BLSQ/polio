import datetime

import time_machine

from django.db import IntegrityError

from iaso import models as m
from iaso.models.json_config import Config
from iaso.test import TestCase
from plugins.polio import models as pm
from plugins.polio.models.base import DOSES_PER_VIAL_CONFIG_SLUG, VaccineStockCalculator


DT = datetime.datetime(2024, 10, 29, 14, 0, 0, 0, tzinfo=datetime.timezone.utc)


@time_machine.travel(DT, tick=False)
class OutgoingStockMovementModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        cls.now = DT
        cls.account = m.Account.objects.create(name="test_account")
        cls.project = m.Project.objects.create(name="Polio", app_id="polio.projects", account=cls.account)
        cls.org_unit_type_country = m.OrgUnitType.objects.create(name="COUNTRY", category="COUNTRY")
        cls.org_unit_type_country.projects.set([cls.project])
        cls.org_unit_type_country.save()
        cls.data_source = m.DataSource.objects.create(name="Default source")
        cls.data_source.projects.set([cls.project])
        cls.source_version_1 = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)

        cls.country = m.OrgUnit.objects.create(
            org_unit_type=cls.org_unit_type_country,
            version=cls.source_version_1,
            name="Testland",
            validation_status=m.OrgUnit.VALIDATION_VALID,
            source_ref="TestlandRef",
        )

        cls.country_2 = m.OrgUnit.objects.create(
            org_unit_type=cls.org_unit_type_country,
            version=cls.source_version_1,
            name="Testland 2",
            validation_status=m.OrgUnit.VALIDATION_VALID,
            source_ref="TestlandRef2",
        )

        cls.campaign = pm.Campaign.objects.create(
            obr_name="Test Campaign",
            country=cls.country,
            account=cls.account,
        )

        cls.campaign_round_1 = pm.Round.objects.create(
            campaign=cls.campaign,
            started_at=datetime.date(2021, 1, 1),
            ended_at=datetime.date(2021, 1, 31),
            number=1,
        )

        cls.vaccine_request_form = pm.VaccineRequestForm.objects.create(
            campaign=cls.campaign,
            vaccine_type=pm.VACCINES[0][0],
            date_vrf_reception=cls.now - datetime.timedelta(days=30),
            date_vrf_signature=cls.now - datetime.timedelta(days=20),
            date_dg_approval=cls.now - datetime.timedelta(days=10),
            quantities_ordered_in_doses=500,
        )

        cls.vaccine_arrival_report = pm.VaccineArrivalReport.objects.create(
            request_form=cls.vaccine_request_form,
            arrival_report_date=cls.now - datetime.timedelta(days=5),
            doses_received=400,
            doses_shipped=400,
            po_number="PO123",
            lot_numbers=["LOT123", "LOT456"],
            expiration_date=cls.now + datetime.timedelta(days=180),
            doses_per_vial=20,
        )

        cls.vaccine_stock = pm.VaccineStock.objects.create(
            account=cls.account,
            country=cls.country,
            vaccine=pm.VACCINES[0][0],
        )

        cls.vaccine_stock_2 = pm.VaccineStock.objects.create(
            account=cls.account,
            country=cls.country_2,
            vaccine=pm.VACCINES[0][0],
        )

        cls.outgoing_stock_movement = pm.OutgoingStockMovement.objects.create(
            campaign=cls.campaign,
            vaccine_stock=cls.vaccine_stock,
            report_date=cls.now - datetime.timedelta(days=3),
            form_a_reception_date=cls.now - datetime.timedelta(days=2),
            usable_vials_used=10,
            lot_numbers=["LOT123"],
            comment="Hello world",
            doses_per_vial=20,
        )

        cls.outgoing_stock_movement_2 = pm.OutgoingStockMovement.objects.create(
            campaign=cls.campaign,
            vaccine_stock=cls.vaccine_stock_2,
            report_date=cls.now - datetime.timedelta(days=3),
            form_a_reception_date=cls.now - datetime.timedelta(days=2),
            usable_vials_used=10,
            doses_per_vial=20,
        )

        cls.destruction_report = pm.DestructionReport.objects.create(
            vaccine_stock=cls.vaccine_stock,
            action="Destroyed due to expiration",
            rrt_destruction_report_reception_date=cls.now - datetime.timedelta(days=1),
            destruction_report_date=cls.now,
            unusable_vials_destroyed=3,
            lot_numbers=["LOT456"],
            comment="Goodbye World",
            doses_per_vial=20,
        )
        cls.incident_report = pm.IncidentReport.objects.create(
            vaccine_stock=cls.vaccine_stock,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.VVM_REACHED_DISCARD_POINT,
            date_of_incident_report=cls.now - datetime.timedelta(days=4),
            incident_report_received_by_rrt=cls.now - datetime.timedelta(days=3),
            unusable_vials=1,  # 1 vial will be moved from usable to unusable
            usable_vials=0,
            doses_per_vial=20,
        )
        cls.incident_report = pm.IncidentReport.objects.create(
            vaccine_stock=cls.vaccine_stock,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.BROKEN,
            date_of_incident_report=cls.now - datetime.timedelta(days=5),
            incident_report_received_by_rrt=cls.now - datetime.timedelta(days=4),
            unusable_vials=0,
            usable_vials=1,
            doses_per_vial=20,
        )
        cls.incident_report = pm.IncidentReport.objects.create(
            vaccine_stock=cls.vaccine_stock,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.PHYSICAL_INVENTORY_ADD,
            date_of_incident_report=cls.now - datetime.timedelta(days=6),
            incident_report_received_by_rrt=cls.now - datetime.timedelta(days=5),
            unusable_vials=0,
            usable_vials=16,
            doses_per_vial=20,
        )
        cls.incident_report = pm.IncidentReport.objects.create(
            vaccine_stock=cls.vaccine_stock,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.PHYSICAL_INVENTORY_ADD,
            date_of_incident_report=cls.now - datetime.timedelta(days=6),
            incident_report_received_by_rrt=cls.now - datetime.timedelta(days=5),
            unusable_vials=20,
            usable_vials=0,
            doses_per_vial=20,
        )

    def test_campaign_and_non_obr_name_cannot_both_be_null(self):
        """Test that the model constraint requiring either campaign or non_obr_name is enforced"""

        new_movement_with_campaign, created = pm.OutgoingStockMovement.objects.get_or_create(
            vaccine_stock=self.vaccine_stock,
            report_date=datetime.date(2025, 1, 1),
            form_a_reception_date=datetime.date(2025, 1, 1),
            usable_vials_used=10,
            campaign=self.campaign,
            doses_per_vial=20,
        )
        self.assertTrue(created)
        new_movement_with_custom_name, created = pm.OutgoingStockMovement.objects.get_or_create(
            vaccine_stock=self.vaccine_stock,
            report_date=datetime.date(2025, 1, 2),
            form_a_reception_date=datetime.date(2025, 1, 2),
            usable_vials_used=10,
            non_obr_name="Test Alternative Campaign Name",
            doses_per_vial=20,
        )
        self.assertTrue(created)

        # This should raise an IntegrityError since neither campaign nor non_obr_name is provided
        with self.assertRaises(IntegrityError):
            pm.OutgoingStockMovement.objects.create(
                vaccine_stock=self.vaccine_stock,
                report_date=datetime.date(2025, 1, 1),
                form_a_reception_date=datetime.date(2025, 1, 1),
                usable_vials_used=10,
                campaign=None,
                non_obr_name=None,
                doses_per_vial=20,
            )

    def test_campaign_and_non_obr_name_cannot_both_have_value(self):
        # This should raise an IntegrityError since campaign nor non_obr_name can't both have value
        with self.assertRaises(IntegrityError):
            pm.OutgoingStockMovement.objects.create(
                vaccine_stock=self.vaccine_stock,
                report_date=datetime.date(2025, 2, 1),
                form_a_reception_date=datetime.date(2025, 2, 1),
                usable_vials_used=10,
                campaign=self.campaign,
                non_obr_name="Another alt campaign",
                doses_per_vial=20,
            )


@time_machine.travel(DT, tick=False)
class VaccineStockCalculatorIpvTestCase(TestCase):
    """IPV/fIPV handling in VaccineStockCalculator (IPV_VACCINE_TYPE_PLAN section 5.2/5.3).

    An IPV stock serves fIPV and combined scopes, since fIPV draws on IPV vials
    and a combination gets one supply chain entry per vaccine.
    """

    @classmethod
    def setUpTestData(cls):
        cls.now = DT
        cls.account = m.Account.objects.create(name="test_account")
        cls.project = m.Project.objects.create(name="Polio", app_id="polio.projects", account=cls.account)
        cls.org_unit_type_country = m.OrgUnitType.objects.create(name="COUNTRY", category="COUNTRY")
        cls.org_unit_type_country.projects.set([cls.project])
        cls.data_source = m.DataSource.objects.create(name="Default source")
        cls.data_source.projects.set([cls.project])
        cls.source_version_1 = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)

        cls.country = m.OrgUnit.objects.create(
            org_unit_type=cls.org_unit_type_country,
            version=cls.source_version_1,
            name="Testland",
            validation_status=m.OrgUnit.VALIDATION_VALID,
            source_ref="TestlandRef",
        )
        cls.district = m.OrgUnit.objects.create(
            org_unit_type=m.OrgUnitType.objects.create(name="DISTRICT", short_name="dis"),
            version=cls.source_version_1,
            name="Testville",
            parent=cls.country,
            validation_status=m.OrgUnit.VALIDATION_VALID,
        )

        cls.ipv_stock = pm.VaccineStock.objects.create(account=cls.account, country=cls.country, vaccine="IPV")
        # The reference date is after both the round and the arrival report.
        cls.end_date = datetime.date(2021, 2, 28)

    def campaign_with_scope(self, obr_name, vaccine):
        """A campaign whose single round is over, with one campaign level scope on `vaccine`."""
        campaign = pm.Campaign.objects.create(
            obr_name=obr_name, country=self.country, account=self.account, separate_scopes_per_round=False
        )
        scope_group = m.Group.objects.create(name=f"{obr_name}_scope", source_version=self.source_version_1)
        scope_group.org_units.set([self.district])
        pm.CampaignScope.objects.create(campaign=campaign, vaccine=vaccine, group=scope_group)
        round_1 = pm.Round.objects.create(
            campaign=campaign,
            started_at=datetime.date(2021, 1, 1),
            ended_at=datetime.date(2021, 1, 31),
            number=1,
        )
        return campaign, round_1

    def ipv_doses_received(self, obr_name, scope_vaccine):
        """Doses an IPV stock sees from a campaign scoped `scope_vaccine`, as of `end_date`."""
        campaign, round_1 = self.campaign_with_scope(obr_name, scope_vaccine)
        request_form = pm.VaccineRequestForm.objects.create(
            campaign=campaign,
            vaccine_type="IPV",
            date_vrf_reception=datetime.date(2020, 12, 1),
            date_vrf_signature=datetime.date(2020, 12, 10),
            date_dg_approval=datetime.date(2020, 12, 20),
            quantities_ordered_in_doses=500,
        )
        request_form.rounds.set([round_1])
        pm.VaccineArrivalReport.objects.create(
            request_form=request_form,
            arrival_report_date=datetime.date(2020, 12, 27),
            doses_received=400,
            doses_shipped=400,
            po_number=f"PO-{obr_name}",
            lot_numbers=["LOT123"],
            expiration_date=datetime.date(2022, 1, 1),
            doses_per_vial=5,  # IPV stock is managed at 5 doses per vial
        )
        calculator = VaccineStockCalculator(self.ipv_stock, self.end_date)
        return calculator.get_total_of_usable_vials()

    def test_ipv_stock_sees_an_fipv_scoped_round(self):
        """Without token matching the fIPV round is not eligible and the stock looks empty."""
        expected_vials_and_doses = (80, 400)
        received_vials_and_doses = self.ipv_doses_received("FIPV_CAMPAIGN", "fIPV")
        self.assertEqual(expected_vials_and_doses, received_vials_and_doses)

    def test_ipv_stock_sees_a_combined_scoped_round(self):
        expected_vials_and_doses = (80, 400)
        received_vials_and_doses = self.ipv_doses_received("IPV_NOPV2_CAMPAIGN", "IPV & nOPV2")
        self.assertEqual(expected_vials_and_doses, received_vials_and_doses)

    def test_ipv_stock_sees_a_plain_ipv_scoped_round(self):
        expected_vials_and_doses = (80, 400)
        received_vials_and_doses = self.ipv_doses_received("IPV_CAMPAIGN", "IPV")
        self.assertEqual(expected_vials_and_doses, received_vials_and_doses)

    def test_ipv_stock_ignores_a_round_without_ipv_in_its_scope(self):
        """The token match must not turn into "any vaccine matches"."""
        expected_vials_and_doses = (0, 0)
        received_vials_and_doses = self.ipv_doses_received("BOPV_CAMPAIGN", "bOPV")
        self.assertEqual(expected_vials_and_doses, received_vials_and_doses)

    def test_presentations_are_read_from_the_ipv_config_key(self):
        Config.objects.create(slug=DOSES_PER_VIAL_CONFIG_SLUG, content={"IPV": [1, 5], "nOPV2": [20, 50]})
        self.ipv_doses_received("IPV_CONFIG_CAMPAIGN", "fIPV")
        calculator = VaccineStockCalculator(self.ipv_stock, self.end_date)

        expected_presentations = ["1", "5"]
        received_presentations = sorted(calculator.get_usable_stock_by_vaccine_presentation().keys())
        self.assertEqual(expected_presentations, received_presentations)

    def test_missing_config_key_returns_none_instead_of_raising(self):
        """An environment whose Config lacks the vaccine key must not 500."""
        Config.objects.create(slug=DOSES_PER_VIAL_CONFIG_SLUG, content={"nOPV2": [20, 50]})
        calculator = VaccineStockCalculator(self.ipv_stock, self.end_date)
        self.assertIsNone(calculator.get_usable_stock_by_vaccine_presentation())
        self.assertIsNone(calculator.get_unusable_stock_by_vaccine_presentation())

    def test_no_config_at_all_returns_none(self):
        calculator = VaccineStockCalculator(self.ipv_stock, self.end_date)
        self.assertIsNone(calculator.get_usable_stock_by_vaccine_presentation())
