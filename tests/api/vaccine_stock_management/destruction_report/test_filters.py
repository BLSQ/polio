from plugins.polio.tests.api.vaccine_stock_management.common import (
    DESTRUCTION_URL,
    StockVariationFiltersAPIBase,
)


class DestructionReportFiltersAPITestCase(StockVariationFiltersAPIBase):
    """`DestructionReportFilter`, on the destruction reports tab of Stock Variation."""

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
