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


class StockVariationFiltersAPITestCase(APITestCase):
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
        expected = status.HTTP_400_BAD_REQUEST

        response = self.client.get(url, {"vaccine_stock": self.stock.pk, **query_params})
        received = response.status_code

        self.assertEqual(expected, received, response.content)

    # Form A

    def test_form_a_no_filter_returns_everything(self):
        expected = [self.form_a_january.pk, self.form_a_february.pk, self.form_a_march.pk]

        received = self.get_ids(FORM_A_URL)

        self.assertCountEqual(expected, received)

    def test_form_a_filter_by_status(self):
        expected_received = [self.form_a_january.pk, self.form_a_march.pk]
        expected_temporary = [self.form_a_february.pk]

        received_received = self.get_ids(FORM_A_URL, status=pm.OutgoingStockMovement.StatusChoices.RECEIVED)
        received_temporary = self.get_ids(FORM_A_URL, status=pm.OutgoingStockMovement.StatusChoices.TEMPORARY)

        self.assertCountEqual(expected_received, received_received)
        self.assertCountEqual(expected_temporary, received_temporary)

    def test_form_a_unknown_status_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, status="not_a_status")

    def test_form_a_filter_by_reception_date_range(self):
        expected_from = [self.form_a_february.pk, self.form_a_march.pk]
        expected_to = [self.form_a_january.pk, self.form_a_february.pk]
        expected_window = [self.form_a_february.pk]

        received_from = self.get_ids(FORM_A_URL, form_a_reception_date_from="2024-02-01")
        received_to = self.get_ids(FORM_A_URL, form_a_reception_date_to="2024-02-28")
        received_window = self.get_ids(
            FORM_A_URL,
            form_a_reception_date_from="2024-02-01",
            form_a_reception_date_to="2024-02-28",
        )

        self.assertCountEqual(expected_from, received_from)
        self.assertCountEqual(expected_to, received_to)
        self.assertCountEqual(expected_window, received_window)

    def test_form_a_reception_date_bounds_are_inclusive(self):
        expected = [self.form_a_january.pk]

        received = self.get_ids(
            FORM_A_URL,
            form_a_reception_date_from="2024-01-15",
            form_a_reception_date_to="2024-01-15",
        )

        self.assertCountEqual(expected, received)

    def test_form_a_filter_by_report_date_range(self):
        expected_from = [self.form_a_march.pk]
        expected_to = [self.form_a_january.pk]

        received_from = self.get_ids(FORM_A_URL, report_date_from="2024-03-01")
        received_to = self.get_ids(FORM_A_URL, report_date_to="2024-01-31")

        self.assertCountEqual(expected_from, received_from)
        self.assertCountEqual(expected_to, received_to)

    def test_form_a_report_date_and_reception_date_are_independent(self):
        # report_date is 5 days before form_a_reception_date for every record, so a window
        # that catches January's report date must not catch its reception date.
        expected = [self.form_a_january.pk]

        received = self.get_ids(
            FORM_A_URL,
            report_date_to="2024-01-12",
            form_a_reception_date_from="2024-01-14",
        )

        self.assertCountEqual(expected, received)

    def test_form_a_filters_combine_with_search(self):
        expected_search = [self.form_a_february.pk]
        # Same search, but a date range that excludes the only match.
        expected_narrowed = []

        received_search = self.get_ids(FORM_A_URL, search="FILTER-2024-OTHER")
        received_narrowed = self.get_ids(FORM_A_URL, search="FILTER-2024-OTHER", report_date_from="2024-03-01")

        self.assertCountEqual(expected_search, received_search)
        self.assertCountEqual(expected_narrowed, received_narrowed)

    def test_form_a_filters_combine_with_ordering(self):
        self.client.force_authenticate(self.user)
        expected = [self.form_a_march.pk, self.form_a_january.pk]

        response = self.client.get(
            FORM_A_URL,
            {
                "vaccine_stock": self.stock.pk,
                "status": pm.OutgoingStockMovement.StatusChoices.RECEIVED,
                "order": "-report_date",
            },
        )
        data = self.assertJSONResponse(response, status.HTTP_200_OK)
        results = data["results"] if isinstance(data, dict) else data
        received = [item["id"] for item in results]

        self.assertEqual(expected, received)

    def test_form_a_filter_by_doses_per_vial(self):
        expected_20 = [self.form_a_january.pk, self.form_a_march.pk]
        expected_50 = [self.form_a_february.pk]

        received_20 = self.get_ids(FORM_A_URL, doses_per_vial=20)
        received_50 = self.get_ids(FORM_A_URL, doses_per_vial=50)

        self.assertCountEqual(expected_20, received_20)
        self.assertCountEqual(expected_50, received_50)

    def test_form_a_doses_per_vial_absent_from_data_returns_nothing(self):
        expected = []

        received = self.get_ids(FORM_A_URL, doses_per_vial=10)

        self.assertCountEqual(expected, received)

    def test_form_a_doses_per_vial_combines_with_status(self):
        expected_matching = [self.form_a_january.pk, self.form_a_march.pk]
        expected_conflicting = []

        received_matching = self.get_ids(
            FORM_A_URL,
            doses_per_vial=20,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
        )
        received_conflicting = self.get_ids(
            FORM_A_URL,
            doses_per_vial=50,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
        )

        self.assertCountEqual(expected_matching, received_matching)
        self.assertCountEqual(expected_conflicting, received_conflicting)

    def test_form_a_non_numeric_doses_per_vial_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, doses_per_vial="twenty")

    def test_form_a_filter_by_round_number(self):
        # Round 1 of two different campaigns: the filter matches the number, not the round.
        expected_round_1 = [self.form_a_january.pk, self.form_a_february.pk]
        expected_round_2 = [self.form_a_march.pk]

        received_round_1 = self.get_ids(FORM_A_URL, round_number=1)
        received_round_2 = self.get_ids(FORM_A_URL, round_number=2)

        self.assertCountEqual(expected_round_1, received_round_1)
        self.assertCountEqual(expected_round_2, received_round_2)

    def test_form_a_round_number_combines_with_search(self):
        expected = [self.form_a_february.pk]

        received = self.get_ids(FORM_A_URL, round_number=1, search="FILTER-2024-OTHER")

        self.assertCountEqual(expected, received)

    def test_form_a_round_number_without_match_returns_nothing(self):
        expected = []

        received = self.get_ids(FORM_A_URL, round_number=3)

        self.assertCountEqual(expected, received)

    def test_form_a_non_numeric_round_number_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, round_number="one")

    def test_form_a_invalid_date_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, report_date_from="not-a-date")

    def test_form_a_filters_do_not_leak_across_vaccine_stocks(self):
        # form_a_other_stock carries the same dates and doses as form_a_january.
        received_by_date = self.get_ids(FORM_A_URL, report_date_from="2000-01-01")
        received_by_doses = self.get_ids(FORM_A_URL, doses_per_vial=20)

        self.assertNotIn(self.form_a_other_stock.pk, received_by_date)
        self.assertNotIn(self.form_a_other_stock.pk, received_by_doses)

    def test_form_a_filters_do_not_leak_across_accounts(self):
        self.client.force_authenticate(self.user)
        expected = []

        response = self.client.get(
            FORM_A_URL,
            {
                "vaccine_stock": self.other_account_stock.pk,
                "doses_per_vial": 20,
                "search": "FILTER-2024-FOREIGN",
            },
        )
        data = self.assertJSONResponse(response, status.HTTP_200_OK)
        results = data["results"] if isinstance(data, dict) else data
        received = [item["id"] for item in results]

        self.assertCountEqual(expected, received)

    def test_form_a_filters_require_permission(self):
        self.client.force_authenticate(self.user_no_perms)
        expected = status.HTTP_403_FORBIDDEN

        response = self.client.get(FORM_A_URL, {"vaccine_stock": self.stock.pk, "doses_per_vial": 20})
        received = response.status_code

        self.assertEqual(expected, received)

    def test_form_a_filters_require_authentication(self):
        self.client.force_authenticate(self.anon)
        expected = status.HTTP_403_FORBIDDEN

        response = self.client.get(FORM_A_URL, {"vaccine_stock": self.stock.pk, "doses_per_vial": 20})
        received = response.status_code

        self.assertEqual(expected, received)

    # Destruction reports

    def test_destruction_no_filter_returns_everything(self):
        expected = [self.destruction_january.pk, self.destruction_march.pk]

        received = self.get_ids(DESTRUCTION_URL)

        self.assertCountEqual(expected, received)

    def test_destruction_filter_by_report_date_range(self):
        expected_from = [self.destruction_march.pk]
        expected_to = [self.destruction_january.pk]

        received_from = self.get_ids(DESTRUCTION_URL, destruction_report_date_from="2024-02-01")
        received_to = self.get_ids(DESTRUCTION_URL, destruction_report_date_to="2024-02-01")

        self.assertCountEqual(expected_from, received_from)
        self.assertCountEqual(expected_to, received_to)

    def test_destruction_filter_by_rrt_reception_date_range(self):
        expected = [self.destruction_january.pk]

        received = self.get_ids(
            DESTRUCTION_URL,
            rrt_reception_date_from="2024-01-01",
            rrt_reception_date_to="2024-01-31",
        )

        self.assertCountEqual(expected, received)

    def test_destruction_filters_combine_with_search(self):
        expected_search = [self.destruction_march.pk]
        expected_narrowed = []

        received_search = self.get_ids(DESTRUCTION_URL, search="Broken")
        received_narrowed = self.get_ids(DESTRUCTION_URL, search="Broken", destruction_report_date_to="2024-02-01")

        self.assertCountEqual(expected_search, received_search)
        self.assertCountEqual(expected_narrowed, received_narrowed)

    def test_destruction_filter_by_doses_per_vial(self):
        expected_20 = [self.destruction_january.pk]
        expected_50 = [self.destruction_march.pk]

        received_20 = self.get_ids(DESTRUCTION_URL, doses_per_vial=20)
        received_50 = self.get_ids(DESTRUCTION_URL, doses_per_vial=50)

        self.assertCountEqual(expected_20, received_20)
        self.assertCountEqual(expected_50, received_50)

    def test_destruction_non_numeric_doses_per_vial_is_rejected(self):
        self.assertBadRequest(DESTRUCTION_URL, doses_per_vial="fifty")

    def test_destruction_invalid_date_is_rejected(self):
        self.assertBadRequest(DESTRUCTION_URL, destruction_report_date_from="31-01-2024")

    # Incident reports

    def test_incident_no_filter_returns_everything(self):
        expected = [self.incident_broken.pk, self.incident_stealing.pk, self.incident_expired.pk]

        received = self.get_ids(INCIDENT_URL)

        self.assertCountEqual(expected, received)

    def test_incident_filter_by_stock_correction(self):
        expected = [self.incident_stealing.pk]

        received = self.get_ids(
            INCIDENT_URL,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.STEALING,
        )

        self.assertCountEqual(expected, received)

    def test_incident_unknown_stock_correction_is_rejected(self):
        self.assertBadRequest(INCIDENT_URL, stock_correction="not_a_correction")

    def test_incident_filter_by_date_of_incident_report_range(self):
        expected_from = [self.incident_stealing.pk, self.incident_expired.pk]
        expected_to = [self.incident_broken.pk, self.incident_stealing.pk]

        received_from = self.get_ids(INCIDENT_URL, date_of_incident_report_from="2024-02-01")
        received_to = self.get_ids(INCIDENT_URL, date_of_incident_report_to="2024-02-28")

        self.assertCountEqual(expected_from, received_from)
        self.assertCountEqual(expected_to, received_to)

    def test_incident_filter_by_rrt_reception_date_range(self):
        expected = [self.incident_stealing.pk]

        received = self.get_ids(
            INCIDENT_URL,
            rrt_reception_date_from="2024-02-01",
            rrt_reception_date_to="2024-02-28",
        )

        self.assertCountEqual(expected, received)

    def test_incident_filters_combine_with_search(self):
        expected_search = [self.incident_expired.pk]
        expected_conflicting = []

        received_search = self.get_ids(INCIDENT_URL, search="Expired batch")
        received_conflicting = self.get_ids(
            INCIDENT_URL,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.BROKEN,
            search="Expired batch",
        )

        self.assertCountEqual(expected_search, received_search)
        self.assertCountEqual(expected_conflicting, received_conflicting)

    def test_incident_filter_by_doses_per_vial(self):
        expected_20 = [self.incident_broken.pk, self.incident_expired.pk]
        expected_50 = [self.incident_stealing.pk]

        received_20 = self.get_ids(INCIDENT_URL, doses_per_vial=20)
        received_50 = self.get_ids(INCIDENT_URL, doses_per_vial=50)

        self.assertCountEqual(expected_20, received_20)
        self.assertCountEqual(expected_50, received_50)

    def test_incident_doses_per_vial_combines_with_stock_correction(self):
        expected_matching = [self.incident_stealing.pk]
        expected_conflicting = []

        received_matching = self.get_ids(
            INCIDENT_URL,
            doses_per_vial=50,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.STEALING,
        )
        received_conflicting = self.get_ids(
            INCIDENT_URL,
            doses_per_vial=20,
            stock_correction=pm.IncidentReport.StockCorrectionChoices.STEALING,
        )

        self.assertCountEqual(expected_matching, received_matching)
        self.assertCountEqual(expected_conflicting, received_conflicting)

    def test_incident_non_numeric_doses_per_vial_is_rejected(self):
        self.assertBadRequest(INCIDENT_URL, doses_per_vial="many")

    def test_incident_invalid_date_is_rejected(self):
        self.assertBadRequest(INCIDENT_URL, rrt_reception_date_from="2024-13-01")
