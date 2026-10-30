from rest_framework import status

from plugins.polio import models as pm
from plugins.polio.tests.api.vaccine_stock_management.common import (
    FORM_A_URL,
    StockVariationFiltersAPIBase,
)


class FormAFiltersAPITestCase(StockVariationFiltersAPIBase):
    """`OutgoingStockMovementFilter`, on the Form A tab of Stock Variation."""

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
