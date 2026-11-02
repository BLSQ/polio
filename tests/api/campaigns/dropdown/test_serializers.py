from iaso.test import SwaggerTestCaseMixin
from plugins.polio.models import (
    VACCINES,
    Campaign,
    CampaignScope,
    RoundScope,
    SubActivity,
    SubActivityScope,
)
from plugins.polio.tests.api.campaigns.dropdown.common import CampaignDropdownAPIBase


class CampaignDropdownSerializersAPITestCase(SwaggerTestCaseMixin, CampaignDropdownAPIBase):
    """What `CampaignDropdownOptionSerializer` and `RoundDropdownOptionSerializer` put in the payload.

    The vaccine lists are the interesting part: they reproduce `Campaign.single_vaccines_extended_list`
    and `Round.single_vaccine_list_extended` off prefetched scope rows, since the model properties
    each cost a query per object.
    """

    def test_payload_matches_the_swagger_schema(self):
        self.client.force_authenticate(self.user)

        received = self.get_payload()

        self.assertResponseCompliantToSwagger(received, "CampaignDropdownOption", as_array=True)

    def test_payload_is_minimal(self):
        self.client.force_authenticate(self.user)

        received = self.get_campaign_payload()

        expected_campaign_keys = [
            "campaign_types",
            "created_at",
            "id",
            "obr_name",
            "rounds",
            "separate_scopes_per_round",
            "vaccines",
        ]
        expected_round_keys = ["ended_at", "has_scope", "id", "number", "on_hold", "started_at", "vaccines"]
        self.assertEqual(expected_campaign_keys, sorted(received.keys()))
        self.assertEqual(expected_round_keys, sorted(received["rounds"][0].keys()))

    def test_payload_values(self):
        self.client.force_authenticate(self.user)

        received = self.get_campaign_payload()

        expected = {
            "id": str(self.campaign.id),
            "obr_name": "Campaign-1",
            "created_at": received["created_at"],
            "campaign_types": [{"id": self.polio_type.pk, "name": self.polio_type.name}],
            "separate_scopes_per_round": False,
            "vaccines": [VACCINES[0][0]],
            "rounds": [
                {
                    "id": round.id,
                    "number": round.number,
                    "on_hold": round.on_hold,
                    "started_at": round.started_at.isoformat(),
                    "ended_at": round.ended_at.isoformat(),
                    "vaccines": [VACCINES[0][0]],
                    "has_scope": False,
                }
                for round in [self.round_1, self.round_2, self.round_3]
            ],
        }
        self.assertEqual(expected, received)

    def test_rounds_are_ordered_by_their_start_date(self):
        """Set by the prefetch in `get_dropdown_queryset`: a serializer `Meta.ordering` is a Django
        model option, not a DRF one, and would be ignored."""
        self.client.force_authenticate(self.user)

        rounds = self.get_campaign_payload()["rounds"]

        expected_numbers = [1, 2, 3]
        self.assertEqual(expected_numbers, [round["number"] for round in rounds])
        self.assertEqual(sorted(round["started_at"] for round in rounds), [round["started_at"] for round in rounds])

    def test_campaign_types_are_serialized(self):
        """Rendered by the integrated campaigns rows, which is why they travel with the options."""
        self.client.force_authenticate(self.user)

        received = self.get_campaign_payload()["campaign_types"]

        expected = [{"id": self.polio_type.pk, "name": self.polio_type.name}]
        self.assertEqual(expected, received)

    def test_rounds_inherit_the_campaign_vaccines_when_scopes_are_not_split(self):
        self.client.force_authenticate(self.user)
        self.assertFalse(self.campaign.separate_scopes_per_round)

        received = self.get_campaign_payload()

        self.assertEqual([VACCINES[0][0]], received["vaccines"])
        for round_data in received["rounds"]:
            self.assertEqual([VACCINES[0][0]], round_data["vaccines"])
            self.assertFalse(round_data["has_scope"])

    def test_rounds_use_their_own_scopes_when_scopes_are_split(self):
        self.client.force_authenticate(self.user)
        self.campaign.separate_scopes_per_round = True
        self.campaign.save()
        round_scope = RoundScope.objects.create(round=self.round_2, vaccine=VACCINES[2][0])
        round_scope.group.org_units.add(self.district)

        received = self.get_campaign_payload()
        rounds_by_number = {round_data["number"]: round_data for round_data in received["rounds"]}

        self.assertEqual([VACCINES[2][0]], rounds_by_number[2]["vaccines"])
        self.assertTrue(rounds_by_number[2]["has_scope"])
        self.assertEqual([], rounds_by_number[1]["vaccines"])
        self.assertFalse(rounds_by_number[1]["has_scope"])

    def test_scopes_without_org_units_name_no_round_vaccine(self):
        """The `group__org_units__isnull=False` of the model properties, reproduced by the
        `group_has_org_units` annotation."""
        self.client.force_authenticate(self.user)
        self.campaign.scopes.all().delete()
        CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[1][0])

        received = self.get_campaign_payload()

        self.assertEqual([], received["vaccines"])
        self.assertEqual([[], [], []], [round["vaccines"] for round in received["rounds"]])

    def test_combined_vaccines_are_split(self):
        self.client.force_authenticate(self.user)
        self.campaign.scopes.all().delete()
        combined_scope = CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[3][0])
        combined_scope.group.org_units.add(self.district)

        received = self.get_campaign_payload()

        expected = sorted([VACCINES[1][0], VACCINES[2][0]])
        self.assertEqual(expected, received["vaccines"])

    def test_vaccines_match_the_model_properties(self):
        """The payload against the properties it replaces, over a mix of campaign, round and
        sub-activity scopes, a combined vaccine and a scope whose group holds no org unit."""
        self.client.force_authenticate(self.user)

        for separate_scopes_per_round in [False, True]:
            with self.subTest(separate_scopes_per_round=separate_scopes_per_round):
                self.campaign.separate_scopes_per_round = separate_scopes_per_round
                self.campaign.save()
                # One pass per scope mode, so clear everything first: `RoundScope` is unique
                # per (round, vaccine) and leftovers from the previous pass would collide.
                self.campaign.scopes.all().delete()
                RoundScope.objects.filter(round__campaign=self.campaign).delete()
                # Cascades to the sub-activities' own scopes.
                SubActivity.objects.filter(round__campaign=self.campaign).delete()

                campaign_scope = CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[0][0])
                campaign_scope.group.org_units.add(self.district)
                combined_scope = CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[3][0])
                combined_scope.group.org_units.add(self.district)
                CampaignScope.objects.create(campaign=self.campaign, vaccine=VACCINES[2][0])

                round_scope = RoundScope.objects.create(round=self.round_2, vaccine=VACCINES[1][0])
                round_scope.group.org_units.add(self.district)
                RoundScope.objects.create(round=self.round_3, vaccine=VACCINES[2][0])

                sub_activity = SubActivity.objects.create(round=self.round_1, name="Mop up")
                sub_activity_scope = SubActivityScope.objects.create(subactivity=sub_activity, vaccine=VACCINES[2][0])
                sub_activity_scope.group.org_units.add(self.district)

                received = self.get_campaign_payload()
                campaign = Campaign.objects.get(pk=self.campaign.pk)

                self.assertEqual(campaign.single_vaccines_extended_list, received["vaccines"])
                self.assertTrue(received["vaccines"])

                rounds_by_number = {round["number"]: round for round in received["rounds"]}
                for round in campaign.rounds.all():
                    with self.subTest(round=round.number):
                        self.assertEqual(
                            round.single_vaccine_list_extended,
                            rounds_by_number[round.number]["vaccines"],
                        )
