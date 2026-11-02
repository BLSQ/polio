from plugins.polio import models as pm
from plugins.polio.tests.api.vaccine_stock_management.common import (
    INCIDENT_URL,
    StockVariationFiltersAPIBase,
)


class IncidentReportFiltersAPITestCase(StockVariationFiltersAPIBase):
    """`IncidentReportFilter`, on the incident reports tab of Stock Variation."""

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
