import datetime

from django.utils import timezone
from rest_framework.status import HTTP_201_CREATED
from rest_framework.test import APIClient

from iaso import models as m
from iaso.models import Account
from iaso.permissions.core_permissions import CORE_FORMS_PERMISSION
from iaso.test import APITestCase
from plugins.polio.models import (
    Campaign,
    CampaignType,
)
from plugins.polio.models.base import VACCINES_BY_VIRUS, ReasonForDelay
from plugins.polio.preparedness.spreadsheet_manager import *
from plugins.polio.tests.api.test import PolioTestCaseMixin


class CreateCampaignAPITestCase(APITestCase, PolioTestCaseMixin):
    data_source: m.DataSource
    source_version_1: m.SourceVersion
    org_unit: m.OrgUnit
    child_org_unit: m.OrgUnit

    @classmethod
    def setUpTestData(cls):
        cls.data_source = m.DataSource.objects.create(name="Default source")
        cls.now = timezone.now()
        cls.source_version_1 = m.SourceVersion.objects.create(data_source=cls.data_source, number=1)
        cls.account = polio_account = Account.objects.create(name="polio", default_version=cls.source_version_1)
        cls.user = cls.create_user_with_profile(
            username="user", account=polio_account, permissions=[CORE_FORMS_PERMISSION]
        )

        cls.country_type = m.OrgUnitType.objects.create(name="COUNTRY", short_name="country")
        cls.district_type = m.OrgUnitType.objects.create(name="DISTRICT", short_name="district")

        cls.org_unit = m.OrgUnit.objects.create(
            org_unit_type=m.OrgUnitType.objects.create(name="Jedi Council", short_name="Cnc"),
            version=cls.source_version_1,
            name="Jedi Council A",
            validation_status=m.OrgUnit.VALIDATION_VALID,
            source_ref="PvtAI4RUMkr",
        )

        cls.child_org_unit = m.OrgUnit.objects.create(
            org_unit_type=m.OrgUnitType.objects.create(name="Jedi Council", short_name="Cnc"),
            version=cls.source_version_1,
            name="Sub Jedi Council A",
            parent_id=cls.org_unit.id,
            validation_status=m.OrgUnit.VALIDATION_VALID,
            source_ref="PvtAI4RUMkr",
        )

        cls.org_units = [
            cls.org_unit,
            cls.child_org_unit,
            m.OrgUnit.objects.create(
                org_unit_type=m.OrgUnitType.objects.create(name="Jedi Council", short_name="Cnc"),
                version=cls.source_version_1,
                name="Jedi Council B",
                validation_status=m.OrgUnit.VALIDATION_VALID,
                source_ref="PvtAI4RUMkr",
            ),
        ]

        cls.user_no_permission = cls.create_user_with_profile(
            username="luke",
            account=polio_account,
            permissions=[CORE_FORMS_PERMISSION],
            org_units=[cls.child_org_unit],
        )
        cls.initial_data = ReasonForDelay.objects.create(
            account=cls.account, key_name="INITIAL_DATA", name_en="Initial data", name_fr="Données initiales"
        )

    def setUp(self):
        """Make sure we have a fresh client at the beginning of each test"""
        self.client = APIClient()

    def test_create_campaign_account_not_mandatory(self):
        """Campaigns ca be created without an account"""
        self.client.force_authenticate(self.user)
        payload = {
            "obr_name": "obr_name",
            "detection_status": "PENDING",
            "rounds": [
                {
                    "number": 0,
                    "started_at": "2021-02-01",
                    "ended_at": "2021-02-20",
                }
            ],
        }
        response = self.client.post("/api/polio/campaigns/", payload, format="json")
        self.assertEqual(Campaign.objects.count(), 1)
        self.assertEqual(response.status_code, 201)

    def test_cannot_create_campaigns_if_not_authenticated(self):
        payload = {
            "account": self.account.pk,
            "obr_name": "obr_name",
            "detection_status": "PENDING",
            "rounds": [
                {
                    "number": 0,
                    "started_at": "2021-02-01",
                    "ended_at": "2021-02-20",
                }
            ],
        }
        response = self.client.post("/api/polio/campaigns/", payload, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Campaign.objects.count(), 0)

    def test_create_campaign(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(Campaign.objects.count(), 0)

        started_at = self.now.strftime("%Y-%m-%d")
        ended_at = (self.now + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        payload = {
            "account": self.account.pk,
            "obr_name": "obr_name",
            "detection_status": "PENDING",
            "rounds": [
                {
                    "number": 0,
                    "started_at": started_at,
                    "ended_at": ended_at,
                }
            ],
        }
        response = self.client.post("/api/polio/campaigns/", payload, format="json")

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Campaign.objects.count(), 1)
        c = Campaign.objects.first()
        self.assertEqual(c.obr_name, "obr_name")
        rounds = c.rounds.all()
        self.assertEqual(1, rounds.count())
        round_zero = rounds.first()
        self.assertEqual(round_zero.number, 0)

        # A chronogram should've been automatically created for the new round.
        self.assertEqual(round_zero.chronograms.valid().count(), 1)
        chronogram = round_zero.chronograms.valid().first()
        self.assertIsNone(chronogram.created_by)

        response = self.client.get(f"/api/polio/campaigns/{c.id}/", payload, format="json")

        r = self.assertJSONResponse(response, 200)
        self.assertEqual(len(r["rounds"]), 1)

    def test_create_campaign_with_round_one(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(Campaign.objects.count(), 0)

        started_at = self.now.strftime("%Y-%m-%d")
        ended_at = (self.now + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        payload = {
            "account": self.account.pk,
            "obr_name": "obr_name",
            "detection_status": "PENDING",
            "rounds": [
                {
                    "number": 1,
                    "started_at": started_at,
                    "ended_at": ended_at,
                }
            ],
        }
        response = self.client.post("/api/polio/campaigns/", payload, format="json")

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Campaign.objects.count(), 1)
        c = Campaign.objects.first()
        self.assertEqual(c.obr_name, "obr_name")
        rounds = c.rounds.all()
        self.assertEqual(1, rounds.count())
        round_zero = rounds.first()
        self.assertEqual(round_zero.number, 1)

        # A chronogram should've been automatically created for the new round.
        self.assertEqual(round_zero.chronograms.valid().count(), 1)
        chronogram = round_zero.chronograms.valid().first()
        self.assertIsNone(chronogram.created_by)

        response = self.client.get(f"/api/polio/campaigns/{c.id}/", payload, format="json")

        r = self.assertJSONResponse(response, 200)
        self.assertEqual(len(r["rounds"]), 1)
        self.assertEqual(r["rounds"][0]["started_at"], started_at)

    def test_create_campaign_with_round_one_and_two(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(Campaign.objects.count(), 0)

        started_at_round_1 = self.now.strftime("%Y-%m-%d")
        ended_at_round_1 = (self.now + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        started_at_round_2 = (self.now + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        ended_at_round_2 = (self.now + datetime.timedelta(days=80)).strftime("%Y-%m-%d")
        payload = {
            "account": self.account.pk,
            "obr_name": "obr_name",
            "detection_status": "PENDING",
            "rounds": [
                {
                    "number": 1,
                    "started_at": started_at_round_1,
                    "ended_at": ended_at_round_1,
                },
                {
                    "number": 2,
                    "started_at": started_at_round_2,
                    "ended_at": ended_at_round_2,
                },
            ],
        }
        response = self.client.post("/api/polio/campaigns/", payload, format="json")

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Campaign.objects.count(), 1)
        c = Campaign.objects.first()
        self.assertEqual(c.obr_name, "obr_name")
        rounds = c.rounds.all().order_by("number")
        self.assertEqual(2, rounds.count())
        self.assertQuerySetEqual(rounds, [1, 2], lambda r: r.number)

        # A chronogram should've been automatically created for each new round.
        round_1 = c.rounds.first()
        self.assertEqual(round_1.chronograms.valid().count(), 1)
        self.assertIsNone(round_1.chronograms.valid().first().created_by)
        round_2 = c.rounds.last()
        self.assertEqual(round_2.chronograms.valid().count(), 1)
        self.assertIsNone(round_2.chronograms.valid().first().created_by)

        response = self.client.get(f"/api/polio/campaigns/{c.id}/", format="json")
        r = self.assertJSONResponse(response, 200)
        self.assertEqual(len(r["rounds"]), 2)
        self.assertEqual(r["rounds"][0]["started_at"], started_at_round_1)
        self.assertEqual(r["rounds"][1]["started_at"], started_at_round_2)

    def test_create_campaign_with_scopes(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(Campaign.objects.count(), 0)

        started_at_round_1 = self.now.strftime("%Y-%m-%d")
        ended_at_round_1 = (self.now + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        started_at_round_2 = (self.now + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        ended_at_round_2 = (self.now + datetime.timedelta(days=80)).strftime("%Y-%m-%d")
        payload = {
            "account": self.account.pk,
            "obr_name": "obr_name",
            "separate_scopes_per_round": False,
            "scopes": [
                {"vaccine": "bOPV", "group": {"org_units": [self.org_unit.id]}},
                {"vaccine": "mOPV2", "group": {"org_units": [self.child_org_unit.id]}},
            ],
            "rounds": [
                {
                    "number": 1,
                    "started_at": started_at_round_1,
                    "ended_at": ended_at_round_1,
                },
                {
                    "number": 2,
                    "started_at": started_at_round_2,
                    "ended_at": ended_at_round_2,
                },
            ],
        }

        response = self.client.post("/api/polio/campaigns/", payload, format="json")

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Campaign.objects.count(), 1)
        c = Campaign.objects.first()
        self.assertEqual(c.obr_name, "obr_name")
        rounds = c.rounds.all().order_by("number")
        self.assertEqual(2, rounds.count())
        self.assertQuerySetEqual(rounds, [1, 2], lambda r: r.number)
        self.assertQuerySetEqual(c.scopes.get(vaccine="bOPV").group.org_units.all(), [self.org_unit])
        self.assertEqual(c.scopes.get(vaccine="bOPV").group.source_version, self.org_unit.version)
        self.assertQuerySetEqual(c.scopes.get(vaccine="mOPV2").group.org_units.all(), [self.child_org_unit])
        # check via the api
        response = self.client.get(f"/api/polio/campaigns/{c.id}/", format="json")
        r = self.assertJSONResponse(response, 200)
        self.assertEqual(len(r["rounds"]), 2)
        self.assertEqual(r["rounds"][0]["started_at"], started_at_round_1)
        self.assertEqual(r["rounds"][0]["districts_count_calculated"], 2)
        self.assertEqual(r["rounds"][1]["started_at"], started_at_round_2)
        self.assertEqual(r["rounds"][1]["districts_count_calculated"], 2)

        # A chronogram should've been automatically created for each new round.
        round_1 = c.rounds.get(id=r["rounds"][0]["id"])
        self.assertEqual(round_1.chronograms.valid().count(), 1)
        self.assertIsNone(round_1.chronograms.valid().first().created_by)
        round_2 = c.rounds.get(id=r["rounds"][1]["id"])
        self.assertEqual(round_2.chronograms.valid().count(), 1)
        self.assertIsNone(round_2.chronograms.valid().first().created_by)

        scope_bOPV = c.scopes.get(vaccine="bOPV")
        scope_mOPV2 = c.scopes.get(vaccine="mOPV2")
        self.assertEqual(
            r["scopes"],
            [
                {
                    "vaccine": "bOPV",
                    "group": {
                        "name": scope_bOPV.group.name,
                        "id": scope_bOPV.group.id,
                        "org_units": [o.id for o in scope_bOPV.group.org_units.all()],
                    },
                },
                {
                    "vaccine": "mOPV2",
                    "group": {
                        "name": scope_mOPV2.group.name,
                        "id": scope_mOPV2.group.id,
                        "org_units": [o.id for o in scope_mOPV2.group.org_units.all()],
                    },
                },
            ],
        )

    def test_create_campaign_with_round_scopes(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(Campaign.objects.count(), 0)

        started_at_round_1 = self.now.strftime("%Y-%m-%d")
        ended_at_round_1 = (self.now + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        started_at_round_2 = (self.now + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        ended_at_round_2 = (self.now + datetime.timedelta(days=80)).strftime("%Y-%m-%d")
        payload = {
            "account": self.account.pk,
            "obr_name": "obr_name",
            "detection_status": "PENDING",
            "separate_scopes_per_round": True,
            "rounds": [
                {
                    "number": 1,
                    "started_at": started_at_round_1,
                    "ended_at": ended_at_round_1,
                    "scopes": [
                        {"vaccine": "bOPV", "group": {"org_units": [self.org_unit.id]}},
                        {
                            "vaccine": "mOPV2",
                            "group": {"org_units": [self.child_org_unit.id]},
                        },
                    ],
                },
                {
                    "number": 2,
                    "started_at": started_at_round_2,
                    "ended_at": ended_at_round_2,
                },
            ],
        }

        response = self.client.post("/api/polio/campaigns/", payload, format="json")

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Campaign.objects.count(), 1)
        c = Campaign.objects.first()
        self.assertEqual(c.obr_name, "obr_name")
        rounds = c.rounds.all().order_by("number")
        self.assertEqual(2, rounds.count())
        self.assertQuerySetEqual(rounds, [1, 2], lambda r: r.number)
        first_round = c.rounds.filter(number=1).first()
        self.assertQuerySetEqual(
            first_round.scopes.get(vaccine="bOPV").group.org_units.all(),
            [self.org_unit],
        )
        self.assertQuerySetEqual(
            first_round.scopes.get(vaccine="mOPV2").group.org_units.all(),
            [self.child_org_unit],
        )
        response = self.client.get(f"/api/polio/campaigns/{c.id}/", format="json")
        r = self.assertJSONResponse(response, 200)
        self.assertEqual(len(r["rounds"]), 2)
        self.assertEqual(r["rounds"][0]["started_at"], started_at_round_1)
        self.assertEqual(r["rounds"][0]["districts_count_calculated"], 2)
        self.assertEqual(r["rounds"][1]["started_at"], started_at_round_2)
        self.assertEqual(r["rounds"][1]["districts_count_calculated"], 0)

        # A chronogram should've been automatically created for each new round.
        round_1 = c.rounds.get(id=r["rounds"][0]["id"])
        self.assertEqual(round_1.chronograms.valid().count(), 1)
        self.assertIsNone(round_1.chronograms.valid().first().created_by)
        round_2 = c.rounds.get(id=r["rounds"][1]["id"])
        self.assertEqual(round_2.chronograms.valid().count(), 1)
        self.assertIsNone(round_2.chronograms.valid().first().created_by)

        round_one = r["rounds"][0]

        self.assertEqual(
            round_one["scopes"],
            [
                {
                    "vaccine": "bOPV",
                    "group": {
                        "name": f"scope {first_round.scopes.get(vaccine='bOPV').id} for round 1 campaign obr_name - bOPV",
                        "id": first_round.scopes.get(vaccine="bOPV").group.id,
                        "org_units": [o.id for o in first_round.scopes.get(vaccine="bOPV").group.org_units.all()],
                    },
                },
                {
                    "vaccine": "mOPV2",
                    "group": {
                        "name": f"scope {first_round.scopes.get(vaccine='mOPV2').id} for round 1 campaign obr_name - mOPV2",
                        "id": first_round.scopes.get(vaccine="mOPV2").group.id,
                        "org_units": [o.id for o in first_round.scopes.get(vaccine="mOPV2").group.org_units.all()],
                    },
                },
            ],
        )

    def test_campaign_creation_without_explicit_campaign_type(self):
        self.client.force_authenticate(self.user)
        payload = {
            "obr_name": "Test Campaign",
            "group": {"name": "Test Group", "org_units": []},
            "is_preventive": True,
            "is_test": False,
            "enable_send_weekly_email": False,
        }
        response = self.client.post("/api/polio/campaigns/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        campaign_id = response.data["id"]
        campaign = Campaign.objects.get(id=campaign_id)
        self.assertEqual(
            campaign.campaign_types.first().name,
            "Polio",
            "Campaign type should default to 'Polio'",
        )

        response = self.client.get(f"/api/polio/campaigns/{campaign.id}/", format="json")
        self.assertEqual(response.status_code, 200, response.content)
        response_data = response.json()

        self.assertIn("campaign_types", response_data)
        campaign_types = response_data["campaign_types"]
        self.assertEqual(len(campaign_types), 1)

    def test_create_campaign_with_explicit_campaign_types(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(Campaign.objects.count(), 0)

        campaign_type1 = CampaignType.objects.create(name="Type1")
        campaign_type2 = CampaignType.objects.create(name="Type2")
        payload = {
            "obr_name": "Campaign with Types",
            "group": {"name": "Test Group", "org_units": []},
            "is_preventive": True,
            "is_test": False,
            "enable_send_weekly_email": False,
            "campaign_types": [campaign_type1.id, campaign_type2.id],
        }

        response = self.client.post("/api/polio/campaigns/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        campaign_id = response.data["id"]
        campaign = Campaign.objects.get(id=campaign_id)

        self.assertEqual(campaign.campaign_types.count(), 2)
        self.assertTrue(campaign.campaign_types.filter(id=campaign_type1.id).exists())
        self.assertTrue(campaign.campaign_types.filter(id=campaign_type2.id).exists())

    def test_can_create_with_orgunits_group(self):
        """Ensure we can create a new campaign object with org units group"""
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/polio/campaigns/",
            data={
                "obr_name": "campaign with org units",
                "scopes": [
                    {
                        "vaccine": "mOPV2",
                        "group": {"org_units": [self.org_units[0].id]},
                    },
                ],
            },
            format="json",
        )

        self.assertJSONResponse(response, HTTP_201_CREATED)
        self.assertEqual(Campaign.objects.count(), 1)
        self.assertEqual(Campaign.objects.get().obr_name, "campaign with org units")
        self.assertEqual(Campaign.objects.get().scopes.first().group.org_units.count(), 1)

    def test_create_round_adds_history(self):
        """Check that adding a round adds a datelog with initial data"""
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/polio/campaigns/",
            data={
                "obr_name": "campaign with org units",
                "rounds": [{"number": 1, "started_at": "2023-03-21", "ended_at": "2023-04-01"}],
            },
            format="json",
        )
        jr = self.assertJSONResponse(response, 201)
        self.assertEqual(len(jr["rounds"]), 1)
        self.assertEqual(len(jr["rounds"][0]["datelogs"]), 1)
        self.assertEqual(jr["rounds"][0]["datelogs"][0]["reason_for_delay"], self.initial_data.key_name)

    def campaign_payload(self, virus, vaccines, obr_name="obr_name", **extra):
        """A creation payload like the other tests', with one campaign level scope per vaccine.

        Each scope takes one of the org units created in setUpTestData, cycling
        through them so two scopes never share a group.
        """
        started_at = self.now.strftime("%Y-%m-%d")
        ended_at = (self.now + datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        return {
            "account": self.account.pk,
            "obr_name": obr_name,
            "detection_status": "PENDING",
            "virus": virus,
            "separate_scopes_per_round": False,
            "scopes": [
                {
                    "vaccine": vaccine,
                    "group": {"org_units": [self.org_units[index % len(self.org_units)].id]},
                }
                for index, vaccine in enumerate(vaccines)
            ],
            "rounds": [{"number": 1, "started_at": started_at, "ended_at": ended_at}],
            **extra,
        }

    def scope_vaccines(self, campaign=None):
        """The vaccines actually stored, sorted so the comparison does not depend on insertion order."""
        campaign = campaign or Campaign.objects.get()
        return sorted(campaign.scopes.values_list("vaccine", flat=True))

    def assertVaccinesRejected(self, response, vaccines, virus):
        """The error names every invalid vaccine and the vaccines the virus does allow."""
        data = self.assertJSONResponse(response, 400)
        expected_errors = [
            f"Vaccine(s) {', '.join(vaccines)} cannot be used for virus {virus}. "
            f"Allowed: {', '.join(VACCINES_BY_VIRUS[virus])}"
        ]
        received_errors = data["non_field_errors"]
        self.assertEqual(expected_errors, received_errors)
        self.assertEqual(0, Campaign.objects.count())

    def test_create_accepts_vaccine_allowed_for_virus(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/polio/campaigns/", self.campaign_payload("cVDPV2", ["nOPV2"]), format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["nOPV2"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_rejects_vaccine_not_allowed_for_virus(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/polio/campaigns/", self.campaign_payload("cVDPV2", ["bOPV"]), format="json")
        self.assertVaccinesRejected(response, ["bOPV"], "cVDPV2")

    def test_create_error_lists_the_allowed_vaccines(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/polio/campaigns/", self.campaign_payload("PV1", ["mOPV2"]), format="json")
        self.assertVaccinesRejected(response, ["mOPV2"], "PV1")

    def test_create_reports_every_invalid_vaccine_sorted(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/polio/campaigns/", self.campaign_payload("cVDPV2", ["mOPV2", "bOPV"]), format="json"
        )
        self.assertVaccinesRejected(response, ["bOPV", "mOPV2"], "cVDPV2")

    def test_create_accepts_ipv_and_fipv_for_every_virus_in_the_matrix(self):
        """IPV and fIPV are allowed whatever the virus, per the plan's matrix."""
        self.client.force_authenticate(self.user)
        for virus in VACCINES_BY_VIRUS:
            for vaccine in ["IPV", "fIPV"]:
                with self.subTest(virus=virus, vaccine=vaccine):
                    obr_name = f"{virus} {vaccine}"
                    payload = self.campaign_payload(virus, [vaccine], obr_name=obr_name)
                    response = self.client.post("/api/polio/campaigns/", payload, format="json")
                    self.assertJSONResponse(response, 201)

                    expected_vaccines = [vaccine]
                    received_vaccines = self.scope_vaccines(Campaign.objects.get(obr_name=obr_name))
                    self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_accepts_combined_vaccine_allowed_for_virus(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/polio/campaigns/", self.campaign_payload("cVDPV2", ["fIPV & nOPV2"]), format="json"
        )
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["fIPV & nOPV2"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_rejects_combined_vaccine_whose_virus_allows_only_part_of_it(self):
        """ "fIPV & nOPV2" is a single value: PV1 allows fIPV but not nOPV2, so it is rejected."""
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/polio/campaigns/", self.campaign_payload("PV1", ["fIPV & nOPV2"]), format="json"
        )
        self.assertVaccinesRejected(response, ["fIPV & nOPV2"], "PV1")

    def test_create_validates_round_scopes(self):
        self.client.force_authenticate(self.user)
        payload = self.campaign_payload("cVDPV2", [])
        payload["separate_scopes_per_round"] = True
        payload["rounds"][0]["scopes"] = [{"vaccine": "bOPV", "group": {"org_units": [self.org_unit.id]}}]
        response = self.client.post("/api/polio/campaigns/", payload, format="json")
        self.assertVaccinesRejected(response, ["bOPV"], "cVDPV2")

    def test_create_without_virus_accepts_any_vaccine(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/polio/campaigns/", self.campaign_payload(None, ["bOPV"]), format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["bOPV"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_with_pv2_accepts_any_vaccine(self):
        """PV2 has no row in the matrix on purpose, so it constrains nothing."""
        self.client.force_authenticate(self.user)
        self.assertNotIn("PV2", VACCINES_BY_VIRUS)
        response = self.client.post("/api/polio/campaigns/", self.campaign_payload("PV2", ["bOPV"]), format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["bOPV"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_validates_a_campaign_submitted_without_any_campaign_type(self):
        """The gate is the virus, not the polio campaign type.

        Legacy campaigns carry no campaign type, and the UI re-submits the empty
        list on save, so gating on the type would skip validation for them.
        """
        self.client.force_authenticate(self.user)
        payload = self.campaign_payload("cVDPV2", ["bOPV"], campaign_types=[])
        response = self.client.post("/api/polio/campaigns/", payload, format="json")
        self.assertVaccinesRejected(response, ["bOPV"], "cVDPV2")

    def test_create_does_not_validate_a_non_polio_campaign_without_virus(self):
        self.client.force_authenticate(self.user)
        measles, _ = CampaignType.objects.get_or_create(name=CampaignType.MEASLES)
        payload = self.campaign_payload(None, ["bOPV"], campaign_types=[measles.id])
        response = self.client.post("/api/polio/campaigns/", payload, format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["bOPV"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)
