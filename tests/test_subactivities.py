import datetime

from django.contrib.auth.models import AnonymousUser
from django.utils.timezone import now

from iaso.models import Account, DataSource, Group, OrgUnit, OrgUnitType, SourceVersion
from iaso.test import APITestCase
from plugins.polio.models import Campaign, Round, SubActivity, SubActivityScope
from plugins.polio.models.base import VACCINES_BY_VIRUS


BASE_URL = "/api/polio/campaigns_subactivities/"


class SubactivitiesAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.data_source = DataSource.objects.create(name="Default source")
        cls.default_source_version = SourceVersion.objects.create(data_source=cls.data_source, number=1)

        cls.now = now()
        cls.account = Account.objects.create(name="Test Account", default_version=cls.default_source_version)
        cls.user = cls.create_user_with_profile(username="Test User", account=cls.account, permissions=[])
        cls.anon = AnonymousUser()

        cls.default_org_unit_type = OrgUnitType.objects.create(name="Jedi Council", short_name="Cnc")
        cls.org_unit = OrgUnit.objects.create(
            name="Test Org Unit",
            version=cls.account.default_version,
            org_unit_type=cls.default_org_unit_type,
            validation_status=OrgUnit.VALIDATION_VALID,
        )

        cls.campaign = Campaign.objects.create(obr_name="Test Campaign", account=cls.account, country=cls.org_unit)

        cls.round = Round.objects.create(campaign=cls.campaign, number=1)
        cls.campaign.rounds.add(cls.round)

        cls.sub_activity = SubActivity.objects.create(
            name="Test SubActivity",
            round=cls.round,
            start_date=datetime.date(2022, 1, 1),
            end_date=datetime.date(2022, 1, 31),
        )

        cls.group = Group.objects.create(name="Test group", source_version=cls.default_source_version)
        cls.group.org_units.add(cls.org_unit)

        cls.sub_activity_scope = SubActivityScope.objects.create(
            subactivity=cls.sub_activity, group=cls.group, vaccine="mOPV2"
        )

    def test_create_sub_activity(self):
        data = {
            "round_number": self.round.number,
            "campaign": self.campaign.obr_name,
            "name": "New SubActivity",
            "start_date": "2022-02-01",
            "end_date": "2022-02-28",
            "scopes": [{"group": {"name": "New Group", "org_units": [self.org_unit.id]}, "vaccine": "mOPV2"}],
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(BASE_URL, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SubActivity.objects.count(), 2)
        self.assertEqual(SubActivityScope.objects.count(), 2)

    def test_anonymous_user_cannot_create_sub_activity(self):
        data = {
            "round_number": self.round.number,
            "campaign": self.campaign.obr_name,
            "name": "New SubActivity",
            "start_date": "2022-02-01",
            "end_date": "2022-02-28",
            "scopes": [{"group": {"name": "New Group", "org_units": [self.org_unit.id]}, "vaccine": "mOPV2"}],
        }
        self.client.force_authenticate(self.anon)
        response = self.client.post(BASE_URL, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_get_sub_activities(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(BASE_URL, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test SubActivity")

    def test_update_sub_activity(self):
        data = {
            "round_number": self.round.number,
            "campaign": self.campaign.obr_name,
            "name": "Updated SubActivity",
            "start_date": "2022-03-01",
            "end_date": "2022-03-31",
            "im_started_at": "2022-04-30",
            "im_ended_at": "2022-05-01",
            "lqas_started_at": "2022-04-29",
            "lqas_ended_at": "2022-05-02",
            "scopes": [{"group": {"name": "Updated Group", "org_units": [self.org_unit.id]}, "vaccine": "mOPV2"}],
        }
        self.client.force_authenticate(self.user)
        response = self.client.put(BASE_URL + str(self.sub_activity.id) + "/", data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SubActivity.objects.get(id=self.sub_activity.id).name, "Updated SubActivity")
        self.assertEqual(SubActivity.objects.get(id=self.sub_activity.id).im_started_at, datetime.date(2022, 4, 30))
        self.assertEqual(SubActivity.objects.get(id=self.sub_activity.id).im_ended_at, datetime.date(2022, 5, 1))
        self.assertEqual(SubActivity.objects.get(id=self.sub_activity.id).lqas_started_at, datetime.date(2022, 4, 29))
        self.assertEqual(SubActivity.objects.get(id=self.sub_activity.id).lqas_ended_at, datetime.date(2022, 5, 2))

    def test_anonymous_user_cannot_delete_sub_activity(self):
        self.client.force_authenticate(self.anon)
        response = self.client.delete(BASE_URL + str(self.sub_activity.id) + "/", format="json")
        self.assertEqual(response.status_code, 403)

    def test_delete_sub_activity(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(BASE_URL + str(self.sub_activity.id) + "/", format="json")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(SubActivity.objects.count(), 0)


class SubActivityVaccineVirusValidationAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.now = now()
        cls.data_source = DataSource.objects.create(name="Default source")
        cls.source_version = SourceVersion.objects.create(data_source=cls.data_source, number=1)
        cls.account = Account.objects.create(name="Test Account", default_version=cls.source_version)
        cls.user = cls.create_user_with_profile(username="Test User", account=cls.account, permissions=[])

        cls.other_account = Account.objects.create(name="Other Account", default_version=cls.source_version)
        cls.other_user = cls.create_user_with_profile(username="Other User", account=cls.other_account, permissions=[])

        cls.org_unit = OrgUnit.objects.create(
            name="Test Org Unit",
            version=cls.source_version,
            org_unit_type=OrgUnitType.objects.create(name="Jedi Council", short_name="Cnc"),
            validation_status=OrgUnit.VALIDATION_VALID,
        )

        # cVDPV2 allows nOPV2, IPV, fIPV and their combinations, but not bOPV or mOPV2.
        cls.campaign = Campaign.objects.create(
            obr_name="Test Campaign", account=cls.account, country=cls.org_unit, virus="cVDPV2"
        )
        cls.round = Round.objects.create(campaign=cls.campaign, number=1)

        # A sub-activity saved before the matrix existed: mOPV2 is not allowed for cVDPV2.
        cls.sub_activity = SubActivity.objects.create(
            name="Test SubActivity",
            round=cls.round,
            start_date=datetime.date(2022, 1, 1),
            end_date=datetime.date(2022, 1, 31),
        )
        cls.group = Group.objects.create(name="Test group", source_version=cls.source_version)
        cls.group.org_units.add(cls.org_unit)
        cls.sub_activity_scope = SubActivityScope.objects.create(
            subactivity=cls.sub_activity, group=cls.group, vaccine="mOPV2"
        )

    def setUp(self):
        self.client.force_authenticate(self.user)

    def scope(self, vaccine, name="New Group"):
        return {"group": {"name": name, "org_units": [self.org_unit.id]}, "vaccine": vaccine}

    def create_payload(self, vaccines):
        return {
            "round_number": self.round.number,
            "campaign": self.campaign.obr_name,
            "name": "New SubActivity",
            "start_date": "2022-02-01",
            "end_date": "2022-02-28",
            "scopes": [self.scope(vaccine, name=f"{vaccine} group") for vaccine in vaccines],
        }

    def update_payload(self, vaccines):
        return {
            "round_number": self.round.number,
            "campaign": self.campaign.obr_name,
            "name": "Updated SubActivity",
            "start_date": "2022-03-01",
            "end_date": "2022-03-31",
            "scopes": [self.scope(vaccine, name=f"{vaccine} group") for vaccine in vaccines],
        }

    def scope_vaccines(self, sub_activity=None):
        """The vaccines actually stored, sorted so the comparison does not depend on insertion order."""
        sub_activity = sub_activity or self.sub_activity
        return sorted(sub_activity.scopes.values_list("vaccine", flat=True))

    def created_sub_activity(self):
        return SubActivity.objects.exclude(id=self.sub_activity.id).get()

    def assertVaccinesRejected(self, response, vaccines):
        """The error names every invalid vaccine and the vaccines the campaign's virus does allow."""
        data = self.assertJSONResponse(response, 400)
        expected_errors = [
            f"Vaccine(s) {', '.join(vaccines)} cannot be used for virus {self.campaign.virus}. "
            f"Allowed: {', '.join(VACCINES_BY_VIRUS[self.campaign.virus])}"
        ]
        received_errors = data["non_field_errors"]
        self.assertEqual(expected_errors, received_errors)

    # Creation

    def test_create_accepts_vaccine_allowed_for_campaign_virus(self):
        response = self.client.post(BASE_URL, self.create_payload(["nOPV2"]), format="json")
        self.assertJSONResponse(response, 201)
        self.assertEqual(2, SubActivity.objects.count())

        expected_vaccines = ["nOPV2"]
        received_vaccines = self.scope_vaccines(self.created_sub_activity())
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_rejects_vaccine_not_allowed_for_campaign_virus(self):
        response = self.client.post(BASE_URL, self.create_payload(["bOPV"]), format="json")
        self.assertVaccinesRejected(response, ["bOPV"])
        self.assertEqual(1, SubActivity.objects.count())

        expected_vaccines = ["mOPV2"]
        received_vaccines = sorted(SubActivityScope.objects.values_list("vaccine", flat=True))
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_accepts_ipv_and_fipv(self):
        for vaccine in ["IPV", "fIPV"]:
            with self.subTest(vaccine=vaccine):
                response = self.client.post(BASE_URL, self.create_payload([vaccine]), format="json")
                data = self.assertJSONResponse(response, 201)

                expected_vaccines = [vaccine]
                received_vaccines = self.scope_vaccines(SubActivity.objects.get(id=data["id"]))
                self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_accepts_combined_vaccine_allowed_for_campaign_virus(self):
        response = self.client.post(BASE_URL, self.create_payload(["fIPV & nOPV2"]), format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["fIPV & nOPV2"]
        received_vaccines = self.scope_vaccines(self.created_sub_activity())
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_rejects_combined_vaccine_whose_virus_allows_only_part_of_it(self):
        """cVDPV2 allows fIPV but not bOPV, so the combined value is rejected as a whole."""
        response = self.client.post(BASE_URL, self.create_payload(["fIPV & bOPV"]), format="json")
        self.assertVaccinesRejected(response, ["fIPV & bOPV"])

    def test_create_reports_every_invalid_vaccine_sorted(self):
        response = self.client.post(BASE_URL, self.create_payload(["mOPV2", "bOPV"]), format="json")
        self.assertVaccinesRejected(response, ["bOPV", "mOPV2"])

    def test_create_without_campaign_virus_accepts_any_vaccine(self):
        self.campaign.virus = None
        self.campaign.save()
        response = self.client.post(BASE_URL, self.create_payload(["bOPV"]), format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["bOPV"]
        received_vaccines = self.scope_vaccines(self.created_sub_activity())
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_with_pv2_campaign_accepts_any_vaccine(self):
        """PV2 has no row in the matrix on purpose, so it constrains nothing."""
        self.assertNotIn("PV2", VACCINES_BY_VIRUS)
        self.campaign.virus = "PV2"
        self.campaign.save()
        response = self.client.post(BASE_URL, self.create_payload(["bOPV"]), format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = ["bOPV"]
        received_vaccines = self.scope_vaccines(self.created_sub_activity())
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_create_without_scopes_is_accepted(self):
        response = self.client.post(BASE_URL, self.create_payload([]), format="json")
        self.assertJSONResponse(response, 201)

        expected_vaccines = []
        received_vaccines = self.scope_vaccines(self.created_sub_activity())
        self.assertEqual(expected_vaccines, received_vaccines)

    # Update: only newly submitted vaccines are checked

    def test_update_keeps_stored_vaccine_not_allowed_for_virus(self):
        self.assertNotIn("mOPV2", VACCINES_BY_VIRUS[self.campaign.virus])
        response = self.client.put(f"{BASE_URL}{self.sub_activity.id}/", self.update_payload(["mOPV2"]), format="json")
        self.assertJSONResponse(response, 200)

        expected_vaccines = ["mOPV2"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_update_rejects_new_vaccine_not_allowed_for_virus(self):
        payload = self.update_payload(["mOPV2", "bOPV"])
        response = self.client.put(f"{BASE_URL}{self.sub_activity.id}/", payload, format="json")
        self.assertVaccinesRejected(response, ["bOPV"])
        self.assertEqual("Test SubActivity", SubActivity.objects.get(id=self.sub_activity.id).name)

        expected_vaccines = ["mOPV2"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)

    def test_update_accepts_new_allowed_vaccine_next_to_a_stored_one(self):
        payload = self.update_payload(["mOPV2", "IPV"])
        response = self.client.put(f"{BASE_URL}{self.sub_activity.id}/", payload, format="json")
        self.assertJSONResponse(response, 200)

        expected_vaccines = ["IPV", "mOPV2"]
        received_vaccines = self.scope_vaccines()
        self.assertEqual(expected_vaccines, received_vaccines)
