import datetime

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
        cls.account = m.Account.objects.create(name="filters_account")
        cls.project = m.Project.objects.create(name="Polio", app_id="polio.filters.projects", account=cls.account)
        cls.org_unit_type_country = m.OrgUnitType.objects.create(name="COUNTRY", category="COUNTRY")
        cls.org_unit_type_country.projects.set([cls.project])
        cls.data_source = m.DataSource.objects.create(name="Filters source")
        cls.data_source.projects.set([cls.project])
        cls.source_version = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)

        cls.user = cls.create_user_with_profile(
            username="filters_user",
            account=cls.account,
            permissions=[
                POLIO_VACCINE_STOCK_MANAGEMENT_READ_PERMISSION,
                POLIO_VACCINE_STOCK_MANAGEMENT_WRITE_PERMISSION,
            ],
        )

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
        # Round 3 exists but no Form A uses it: it must stay out of the dropdown.
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

    def get_ids(self, url, **query_params):
        self.client.force_authenticate(self.user)
        response = self.client.get(url, {"vaccine_stock": self.stock.pk, **query_params})
        data = self.assertJSONResponse(response, 200)
        results = data["results"] if isinstance(data, dict) else data
        return {item["id"] for item in results}

    def assertBadRequest(self, url, **query_params):
        self.client.force_authenticate(self.user)
        response = self.client.get(url, {"vaccine_stock": self.stock.pk, **query_params})
        self.assertEqual(response.status_code, 400, response.content)

    # Form A

    def test_form_a_no_filter_returns_everything(self):
        self.assertEqual(
            self.get_ids(FORM_A_URL),
            {self.form_a_january.pk, self.form_a_february.pk, self.form_a_march.pk},
        )

    def test_form_a_filter_by_status(self):
        self.assertEqual(
            self.get_ids(FORM_A_URL, status=pm.OutgoingStockMovement.StatusChoices.RECEIVED),
            {self.form_a_january.pk, self.form_a_march.pk},
        )
        self.assertEqual(
            self.get_ids(FORM_A_URL, status=pm.OutgoingStockMovement.StatusChoices.TEMPORARY),
            {self.form_a_february.pk},
        )

    def test_form_a_unknown_status_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, status="not_a_status")

    def test_form_a_filter_by_reception_date_range(self):
        self.assertEqual(
            self.get_ids(FORM_A_URL, form_a_reception_date_from="2024-02-01"),
            {self.form_a_february.pk, self.form_a_march.pk},
        )
        self.assertEqual(
            self.get_ids(FORM_A_URL, form_a_reception_date_to="2024-02-28"),
            {self.form_a_january.pk, self.form_a_february.pk},
        )
        self.assertEqual(
            self.get_ids(
                FORM_A_URL,
                form_a_reception_date_from="2024-02-01",
                form_a_reception_date_to="2024-02-28",
            ),
            {self.form_a_february.pk},
        )

    def test_form_a_reception_date_bounds_are_inclusive(self):
        self.assertEqual(
            self.get_ids(
                FORM_A_URL,
                form_a_reception_date_from="2024-01-15",
                form_a_reception_date_to="2024-01-15",
            ),
            {self.form_a_january.pk},
        )

    def test_form_a_filter_by_report_date_range(self):
        self.assertEqual(
            self.get_ids(FORM_A_URL, report_date_from="2024-03-01"),
            {self.form_a_march.pk},
        )
        self.assertEqual(
            self.get_ids(FORM_A_URL, report_date_to="2024-01-31"),
            {self.form_a_january.pk},
        )

    def test_form_a_report_date_and_reception_date_are_independent(self):
        # report_date is 5 days before form_a_reception_date for every record, so a window
        # that catches January's report date must not catch its reception date.
        self.assertEqual(
            self.get_ids(FORM_A_URL, report_date_to="2024-01-12", form_a_reception_date_from="2024-01-14"),
            {self.form_a_january.pk},
        )

    def test_form_a_filters_combine_with_search(self):
        self.assertEqual(
            self.get_ids(FORM_A_URL, search="FILTER-2024-OTHER"),
            {self.form_a_february.pk},
        )
        # Same search, but a date range that excludes the only match.
        self.assertEqual(
            self.get_ids(FORM_A_URL, search="FILTER-2024-OTHER", report_date_from="2024-03-01"),
            set(),
        )

    def test_form_a_filters_combine_with_ordering(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(
            FORM_A_URL,
            {
                "vaccine_stock": self.stock.pk,
                "status": pm.OutgoingStockMovement.StatusChoices.RECEIVED,
                "order": "-report_date",
            },
        )
        data = self.assertJSONResponse(response, 200)
        results = data["results"] if isinstance(data, dict) else data
        self.assertEqual(
            [item["id"] for item in results],
            [self.form_a_march.pk, self.form_a_january.pk],
        )

    def test_form_a_filter_by_doses_per_vial(self):
        self.assertEqual(
            self.get_ids(FORM_A_URL, doses_per_vial=20),
            {self.form_a_january.pk, self.form_a_march.pk},
        )
        self.assertEqual(
            self.get_ids(FORM_A_URL, doses_per_vial=50),
            {self.form_a_february.pk},
        )

    def test_form_a_doses_per_vial_absent_from_data_returns_nothing(self):
        self.assertEqual(self.get_ids(FORM_A_URL, doses_per_vial=10), set())

    def test_form_a_doses_per_vial_combines_with_status(self):
        self.assertEqual(
            self.get_ids(
                FORM_A_URL,
                doses_per_vial=20,
                status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            ),
            {self.form_a_january.pk, self.form_a_march.pk},
        )
        self.assertEqual(
            self.get_ids(
                FORM_A_URL,
                doses_per_vial=50,
                status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            ),
            set(),
        )

    def test_form_a_non_numeric_doses_per_vial_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, doses_per_vial="twenty")

    def test_form_a_filter_by_round_number(self):
        # Round 1 of two different campaigns: the filter matches the number, not the round.
        self.assertEqual(
            self.get_ids(FORM_A_URL, round_number=1),
            {self.form_a_january.pk, self.form_a_february.pk},
        )
        self.assertEqual(
            self.get_ids(FORM_A_URL, round_number=2),
            {self.form_a_march.pk},
        )

    def test_form_a_round_number_combines_with_search(self):
        self.assertEqual(
            self.get_ids(FORM_A_URL, round_number=1, search="FILTER-2024-OTHER"),
            {self.form_a_february.pk},
        )

    def test_form_a_round_number_without_match_returns_nothing(self):
        self.assertEqual(self.get_ids(FORM_A_URL, round_number=3), set())

    def test_form_a_non_numeric_round_number_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, round_number="one")

    # Round dropdown options

    def get_round_numbers(self, **query_params):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{FORM_A_URL}round_numbers/", query_params)
        return self.assertJSONResponse(response, 200)

    def test_round_numbers_lists_only_rounds_in_use_for_the_stock(self):
        # round_3_unused has a Form A on the other stock only, so it must not show up here.
        self.assertEqual(self.get_round_numbers(vaccine_stock=self.stock.pk), [1, 2])

    def test_round_numbers_are_distinct_and_sorted(self):
        pm.OutgoingStockMovement.objects.create(
            campaign=self.campaign,
            vaccine_stock=self.stock,
            round=self.round_2,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            report_date=datetime.date(2024, 4, 10),
            form_a_reception_date=datetime.date(2024, 4, 15),
            usable_vials_used=5,
            doses_per_vial=20,
        )
        self.assertEqual(self.get_round_numbers(vaccine_stock=self.stock.pk), [1, 2])

    def test_round_numbers_of_another_stock(self):
        self.assertEqual(self.get_round_numbers(vaccine_stock=self.other_stock.pk), [3])

    def test_round_numbers_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get(f"{FORM_A_URL}round_numbers/", {"vaccine_stock": self.stock.pk})
        self.assertIn(response.status_code, (401, 403))

    def test_form_a_invalid_date_is_rejected(self):
        self.assertBadRequest(FORM_A_URL, report_date_from="not-a-date")

    def test_form_a_filters_do_not_leak_across_vaccine_stocks(self):
        # Same dates and doses as form_a_january, but on another stock.
        self.assertNotIn(
            self.form_a_other_stock.pk,
            self.get_ids(FORM_A_URL, report_date_from="2000-01-01"),
        )
        self.assertNotIn(
            self.form_a_other_stock.pk,
            self.get_ids(FORM_A_URL, doses_per_vial=20),
        )

    # Destruction reports

    def test_destruction_no_filter_returns_everything(self):
        self.assertEqual(
            self.get_ids(DESTRUCTION_URL),
            {self.destruction_january.pk, self.destruction_march.pk},
        )

    def test_destruction_filter_by_report_date_range(self):
        self.assertEqual(
            self.get_ids(DESTRUCTION_URL, destruction_report_date_from="2024-02-01"),
            {self.destruction_march.pk},
        )
        self.assertEqual(
            self.get_ids(DESTRUCTION_URL, destruction_report_date_to="2024-02-01"),
            {self.destruction_january.pk},
        )

    def test_destruction_filter_by_rrt_reception_date_range(self):
        self.assertEqual(
            self.get_ids(
                DESTRUCTION_URL,
                rrt_reception_date_from="2024-01-01",
                rrt_reception_date_to="2024-01-31",
            ),
            {self.destruction_january.pk},
        )

    def test_destruction_filters_combine_with_search(self):
        self.assertEqual(
            self.get_ids(DESTRUCTION_URL, search="Broken"),
            {self.destruction_march.pk},
        )
        self.assertEqual(
            self.get_ids(DESTRUCTION_URL, search="Broken", destruction_report_date_to="2024-02-01"),
            set(),
        )

    def test_destruction_filter_by_doses_per_vial(self):
        self.assertEqual(
            self.get_ids(DESTRUCTION_URL, doses_per_vial=20),
            {self.destruction_january.pk},
        )
        self.assertEqual(
            self.get_ids(DESTRUCTION_URL, doses_per_vial=50),
            {self.destruction_march.pk},
        )

    def test_destruction_non_numeric_doses_per_vial_is_rejected(self):
        self.assertBadRequest(DESTRUCTION_URL, doses_per_vial="fifty")

    def test_destruction_invalid_date_is_rejected(self):
        self.assertBadRequest(DESTRUCTION_URL, destruction_report_date_from="31-01-2024")

    # Incident reports

    def test_incident_no_filter_returns_everything(self):
        self.assertEqual(
            self.get_ids(INCIDENT_URL),
            {self.incident_broken.pk, self.incident_stealing.pk, self.incident_expired.pk},
        )

    def test_incident_filter_by_stock_correction(self):
        self.assertEqual(
            self.get_ids(
                INCIDENT_URL,
                stock_correction=pm.IncidentReport.StockCorrectionChoices.STEALING,
            ),
            {self.incident_stealing.pk},
        )

    def test_incident_unknown_stock_correction_is_rejected(self):
        self.assertBadRequest(INCIDENT_URL, stock_correction="not_a_correction")

    def test_incident_filter_by_date_of_incident_report_range(self):
        self.assertEqual(
            self.get_ids(INCIDENT_URL, date_of_incident_report_from="2024-02-01"),
            {self.incident_stealing.pk, self.incident_expired.pk},
        )
        self.assertEqual(
            self.get_ids(INCIDENT_URL, date_of_incident_report_to="2024-02-28"),
            {self.incident_broken.pk, self.incident_stealing.pk},
        )

    def test_incident_filter_by_rrt_reception_date_range(self):
        self.assertEqual(
            self.get_ids(
                INCIDENT_URL,
                rrt_reception_date_from="2024-02-01",
                rrt_reception_date_to="2024-02-28",
            ),
            {self.incident_stealing.pk},
        )

    def test_incident_filters_combine_with_search(self):
        self.assertEqual(
            self.get_ids(INCIDENT_URL, search="Expired batch"),
            {self.incident_expired.pk},
        )
        self.assertEqual(
            self.get_ids(
                INCIDENT_URL,
                stock_correction=pm.IncidentReport.StockCorrectionChoices.BROKEN,
                search="Expired batch",
            ),
            set(),
        )

    def test_incident_filter_by_doses_per_vial(self):
        self.assertEqual(
            self.get_ids(INCIDENT_URL, doses_per_vial=20),
            {self.incident_broken.pk, self.incident_expired.pk},
        )
        self.assertEqual(
            self.get_ids(INCIDENT_URL, doses_per_vial=50),
            {self.incident_stealing.pk},
        )

    def test_incident_doses_per_vial_combines_with_stock_correction(self):
        self.assertEqual(
            self.get_ids(
                INCIDENT_URL,
                doses_per_vial=50,
                stock_correction=pm.IncidentReport.StockCorrectionChoices.STEALING,
            ),
            {self.incident_stealing.pk},
        )
        self.assertEqual(
            self.get_ids(
                INCIDENT_URL,
                doses_per_vial=20,
                stock_correction=pm.IncidentReport.StockCorrectionChoices.STEALING,
            ),
            set(),
        )

    def test_incident_non_numeric_doses_per_vial_is_rejected(self):
        self.assertBadRequest(INCIDENT_URL, doses_per_vial="many")

    def test_incident_invalid_date_is_rejected(self):
        self.assertBadRequest(INCIDENT_URL, rrt_reception_date_from="2024-13-01")
