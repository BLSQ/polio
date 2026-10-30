import datetime

from rest_framework import status

from iaso import models as m
from iaso.test import APITestCase
from plugins.polio import models as pm
from plugins.polio.permissions import (
    POLIO_VACCINE_STOCK_MANAGEMENT_READ_PERMISSION,
    POLIO_VACCINE_STOCK_MANAGEMENT_WRITE_PERMISSION,
)


BASE_URL_SUB_RESOURCES = "/api/polio/vaccine/stock/"

FORM_A_URL = f"{BASE_URL_SUB_RESOURCES}outgoing_stock_movement/"
DESTRUCTION_URL = f"{BASE_URL_SUB_RESOURCES}destruction_report/"
INCIDENT_URL = f"{BASE_URL_SUB_RESOURCES}incident_report/"


class StockVariationFiltersAPIBase(APITestCase):
    """Fixtures and helpers shared by the Form A, destruction and incident filter tests.

    Holds no test of its own: each tab subclasses it in its own `test_filters.py`.
    """

    @classmethod
    def setUpTestData(cls):
        cls.account, cls.data_source, cls.source_version, cls.project = cls.create_account_datasource_version_project(
            "Filters source", "filters_account", "Filters project"
        )
        cls.user, cls.anon, cls.user_no_perms = cls.create_base_users(
            cls.account,
            [
                POLIO_VACCINE_STOCK_MANAGEMENT_READ_PERMISSION,
                POLIO_VACCINE_STOCK_MANAGEMENT_WRITE_PERMISSION,
            ],
        )

        cls.org_unit_type_country = m.OrgUnitType.objects.create(name="COUNTRY", category="COUNTRY")
        cls.org_unit_type_country.projects.set([cls.project])
        cls.country = m.OrgUnit.objects.create(
            org_unit_type=cls.org_unit_type_country,
            version=cls.source_version,
            name="Testland",
            validation_status=m.OrgUnit.VALIDATION_VALID,
            source_ref="TestlandRef",
        )

        cls.campaign = pm.Campaign.objects.create(
            obr_name="FILTER-2024-MAIN",
            country=cls.country,
            account=cls.account,
        )
        cls.round_1 = pm.Round.objects.create(
            campaign=cls.campaign,
            number=1,
            started_at=datetime.date(2024, 1, 1),
            ended_at=datetime.date(2024, 1, 5),
        )
        cls.round_2 = pm.Round.objects.create(
            campaign=cls.campaign,
            number=2,
            started_at=datetime.date(2024, 3, 1),
            ended_at=datetime.date(2024, 3, 5),
        )
        cls.other_campaign = pm.Campaign.objects.create(
            obr_name="FILTER-2024-OTHER",
            country=cls.country,
            account=cls.account,
        )
        cls.other_round_1 = pm.Round.objects.create(
            campaign=cls.other_campaign,
            number=1,
            started_at=datetime.date(2024, 2, 1),
            ended_at=datetime.date(2024, 2, 5),
        )
        cls.round_3_unused = pm.Round.objects.create(
            campaign=cls.campaign,
            number=3,
            started_at=datetime.date(2024, 5, 1),
            ended_at=datetime.date(2024, 5, 5),
        )

        cls.stock = pm.VaccineStock.objects.create(
            account=cls.account,
            country=cls.country,
            vaccine=pm.VACCINES[1][0],
        )
        # A second stock, to prove the filters never reach across stocks.
        cls.other_stock = pm.VaccineStock.objects.create(
            account=cls.account,
            country=cls.country,
            vaccine=pm.VACCINES[2][0],
        )
        cls.form_a_other_stock = pm.OutgoingStockMovement.objects.create(
            campaign=cls.campaign,
            vaccine_stock=cls.other_stock,
            round=cls.round_3_unused,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            report_date=datetime.date(2024, 1, 10),
            form_a_reception_date=datetime.date(2024, 1, 15),
            usable_vials_used=10,
            doses_per_vial=20,
        )

        # Form A: two statuses, dates one month apart.
        cls.form_a_january = pm.OutgoingStockMovement.objects.create(
            campaign=cls.campaign,
            vaccine_stock=cls.stock,
            round=cls.round_1,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            report_date=datetime.date(2024, 1, 10),
            form_a_reception_date=datetime.date(2024, 1, 15),
            usable_vials_used=10,
            doses_per_vial=20,
        )
        cls.form_a_february = pm.OutgoingStockMovement.objects.create(
            campaign=cls.other_campaign,
            vaccine_stock=cls.stock,
            round=cls.other_round_1,
            status=pm.OutgoingStockMovement.StatusChoices.TEMPORARY,
            report_date=datetime.date(2024, 2, 10),
            form_a_reception_date=datetime.date(2024, 2, 15),
            usable_vials_used=20,
            doses_per_vial=50,
        )
        cls.form_a_march = pm.OutgoingStockMovement.objects.create(
            campaign=cls.campaign,
            vaccine_stock=cls.stock,
            round=cls.round_2,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            report_date=datetime.date(2024, 3, 10),
            form_a_reception_date=datetime.date(2024, 3, 15),
            usable_vials_used=30,
            doses_per_vial=20,
        )

        cls.destruction_january = pm.DestructionReport.objects.create(
            vaccine_stock=cls.stock,
            action="Expired vials",
            destruction_report_date=datetime.date(2024, 1, 20),
            rrt_destruction_report_reception_date=datetime.date(2024, 1, 25),
            unusable_vials_destroyed=3,
            doses_per_vial=20,
        )
        cls.destruction_march = pm.DestructionReport.objects.create(
            vaccine_stock=cls.stock,
            action="Broken vials",
            destruction_report_date=datetime.date(2024, 3, 20),
            rrt_destruction_report_reception_date=datetime.date(2024, 3, 25),
            unusable_vials_destroyed=5,
            doses_per_vial=50,
        )

        cls.incident_broken = pm.IncidentReport.objects.create(
            vaccine_stock=cls.stock,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.BROKEN,
            title="Broken in transit",
            date_of_incident_report=datetime.date(2024, 1, 5),
            incident_report_received_by_rrt=datetime.date(2024, 1, 10),
            usable_vials=0,
            unusable_vials=2,
            doses_per_vial=20,
        )
        cls.incident_stealing = pm.IncidentReport.objects.create(
            vaccine_stock=cls.stock,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.STEALING,
            title="Stolen at the depot",
            date_of_incident_report=datetime.date(2024, 2, 5),
            incident_report_received_by_rrt=datetime.date(2024, 2, 10),
            usable_vials=0,
            unusable_vials=4,
            doses_per_vial=50,
        )
        cls.incident_expired = pm.IncidentReport.objects.create(
            vaccine_stock=cls.stock,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.VACCINE_EXPIRED,
            title="Expired batch",
            date_of_incident_report=datetime.date(2024, 3, 5),
            incident_report_received_by_rrt=datetime.date(2024, 3, 10),
            usable_vials=0,
            unusable_vials=6,
            doses_per_vial=20,
        )

        (
            cls.other_account,
            cls.other_data_source,
            cls.other_source_version,
            cls.other_project,
        ) = cls.create_account_datasource_version_project("Other source", "other_filters_account", "Other project")
        cls.other_account_org_unit_type = m.OrgUnitType.objects.create(name="COUNTRY OTHER", category="COUNTRY")
        cls.other_account_org_unit_type.projects.set([cls.other_project])
        cls.other_account_country = m.OrgUnit.objects.create(
            org_unit_type=cls.other_account_org_unit_type,
            version=cls.other_source_version,
            name="Otherland",
            validation_status=m.OrgUnit.VALIDATION_VALID,
            source_ref="OtherlandRef",
        )
        cls.other_account_campaign = pm.Campaign.objects.create(
            obr_name="FILTER-2024-FOREIGN",
            country=cls.other_account_country,
            account=cls.other_account,
        )
        cls.other_account_round = pm.Round.objects.create(
            campaign=cls.other_account_campaign,
            number=1,
            started_at=datetime.date(2024, 1, 1),
            ended_at=datetime.date(2024, 1, 5),
        )
        cls.other_account_stock = pm.VaccineStock.objects.create(
            account=cls.other_account,
            country=cls.other_account_country,
            vaccine=pm.VACCINES[1][0],
        )
        cls.other_account_form_a = pm.OutgoingStockMovement.objects.create(
            campaign=cls.other_account_campaign,
            vaccine_stock=cls.other_account_stock,
            round=cls.other_account_round,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            report_date=datetime.date(2024, 1, 10),
            form_a_reception_date=datetime.date(2024, 1, 15),
            usable_vials_used=10,
            doses_per_vial=20,
        )

    def get_ids(self, url, **query_params):
        """The ids returned for a filtered list call, as a list so duplicates stay visible."""
        self.client.force_authenticate(self.user)
        response = self.client.get(url, {"vaccine_stock": self.stock.pk, **query_params})
        data = self.assertJSONResponse(response, status.HTTP_200_OK)
        results = data["results"] if isinstance(data, dict) else data
        return [item["id"] for item in results]

    def assertBadRequest(self, url, **query_params):
        self.client.force_authenticate(self.user)
        response = self.client.get(url, {"vaccine_stock": self.stock.pk, **query_params})
        self.assertJSONResponse(response, status.HTTP_400_BAD_REQUEST)
