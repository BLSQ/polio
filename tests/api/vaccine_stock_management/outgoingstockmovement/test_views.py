import datetime

from rest_framework import status

from iaso import models as m
from iaso.test import APITestCase
from plugins.polio import models as pm
from plugins.polio.permissions import (
    POLIO_VACCINE_STOCK_MANAGEMENT_READ_PERMISSION,
    POLIO_VACCINE_STOCK_MANAGEMENT_WRITE_PERMISSION,
)


FORM_A_URL = "/api/polio/vaccine/stock/outgoing_stock_movement/"
ROUND_NUMBERS_URL = f"{FORM_A_URL}round_numbers/"


class OutgoingStockMovementRoundNumbersAPITestCase(APITestCase):
    """The `round_numbers` action feeding the Form A round dropdown."""

    @classmethod
    def setUpTestData(cls):
        cls.account, cls.data_source, cls.source_version, cls.project = cls.create_account_datasource_version_project(
            "Round numbers source", "round_numbers_account", "Round numbers project"
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
            obr_name="ROUNDS-2024-MAIN",
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
        # Round 3 is used by the other stock only: it must stay out of cls.stock's dropdown.
        cls.round_3 = pm.Round.objects.create(
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
        cls.other_stock = pm.VaccineStock.objects.create(
            account=cls.account,
            country=cls.country,
            vaccine=pm.VACCINES[2][0],
        )

        cls.create_form_a(cls.campaign, cls.stock, cls.round_1, datetime.date(2024, 1, 10))
        cls.create_form_a(cls.campaign, cls.stock, cls.round_2, datetime.date(2024, 3, 10))
        cls.create_form_a(cls.campaign, cls.other_stock, cls.round_3, datetime.date(2024, 5, 10))

        # A separate tenant, with its own rounds, to prove the action never crosses accounts.
        (
            cls.other_account,
            cls.other_data_source,
            cls.other_source_version,
            cls.other_project,
        ) = cls.create_account_datasource_version_project(
            "Other source", "other_round_numbers_account", "Other project"
        )
        cls.other_account_user = cls.create_user_with_profile(
            username="other_account_user",
            account=cls.other_account,
            permissions=[
                POLIO_VACCINE_STOCK_MANAGEMENT_READ_PERMISSION,
                POLIO_VACCINE_STOCK_MANAGEMENT_WRITE_PERMISSION,
            ],
        )
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
            obr_name="ROUNDS-2024-FOREIGN",
            country=cls.other_account_country,
            account=cls.other_account,
        )
        cls.other_account_round = pm.Round.objects.create(
            campaign=cls.other_account_campaign,
            number=7,
            started_at=datetime.date(2024, 7, 1),
            ended_at=datetime.date(2024, 7, 5),
        )
        cls.other_account_stock = pm.VaccineStock.objects.create(
            account=cls.other_account,
            country=cls.other_account_country,
            vaccine=pm.VACCINES[1][0],
        )
        cls.create_form_a(
            cls.other_account_campaign,
            cls.other_account_stock,
            cls.other_account_round,
            datetime.date(2024, 7, 10),
        )

    @classmethod
    def create_form_a(cls, campaign, vaccine_stock, round, report_date):
        return pm.OutgoingStockMovement.objects.create(
            campaign=campaign,
            vaccine_stock=vaccine_stock,
            round=round,
            status=pm.OutgoingStockMovement.StatusChoices.RECEIVED,
            report_date=report_date,
            form_a_reception_date=report_date + datetime.timedelta(days=5),
            usable_vials_used=10,
            doses_per_vial=20,
        )

    def get_round_numbers(self, user, vaccine_stock_id):
        self.client.force_authenticate(user)
        response = self.client.get(ROUND_NUMBERS_URL, {"vaccine_stock": vaccine_stock_id})
        return self.assertJSONResponse(response, status.HTTP_200_OK)

    def test_round_numbers_lists_only_rounds_in_use_for_the_stock(self):
        expected = [1, 2]

        received = self.get_round_numbers(self.user, self.stock.pk)

        self.assertCountEqual(expected, received)

    def test_round_numbers_are_distinct_and_sorted(self):
        # A second Form A on round 2 must not produce a duplicate entry.
        self.create_form_a(self.campaign, self.stock, self.round_2, datetime.date(2024, 4, 10))
        expected = [1, 2]

        received = self.get_round_numbers(self.user, self.stock.pk)

        # Ordering is part of the contract here, so this one compares the lists as they are.
        self.assertEqual(expected, received)

    def test_round_numbers_of_another_stock(self):
        expected = [3]

        received = self.get_round_numbers(self.user, self.other_stock.pk)

        self.assertCountEqual(expected, received)

    def test_round_numbers_without_a_stock_lists_every_round_of_the_account(self):
        self.client.force_authenticate(self.user)
        expected = [1, 2, 3]

        response = self.client.get(ROUND_NUMBERS_URL)
        received = self.assertJSONResponse(response, status.HTTP_200_OK)

        self.assertCountEqual(expected, received)

    def test_round_numbers_does_not_cross_accounts(self):
        expected = []

        received = self.get_round_numbers(self.user, self.other_account_stock.pk)

        self.assertCountEqual(expected, received)

    def test_round_numbers_of_another_account_user_sees_only_their_own(self):
        expected = [7]

        received = self.get_round_numbers(self.other_account_user, self.other_account_stock.pk)

        self.assertCountEqual(expected, received)

    def test_round_numbers_requires_authentication(self):
        self.client.force_authenticate(self.anon)
        expected = status.HTTP_403_FORBIDDEN

        response = self.client.get(ROUND_NUMBERS_URL, {"vaccine_stock": self.stock.pk})
        received = response.status_code

        self.assertEqual(expected, received)

    def test_round_numbers_requires_permission(self):
        self.client.force_authenticate(self.user_no_perms)
        expected = status.HTTP_403_FORBIDDEN

        response = self.client.get(ROUND_NUMBERS_URL, {"vaccine_stock": self.stock.pk})
        received = response.status_code

        self.assertEqual(expected, received)
