from unittest import mock

from django.http import HttpResponse
from django.test import override_settings
from rest_framework import status

from iaso.test import TestCase


EMBEDDED_PATHS = [
    "/dashboard/polio/embeddedCalendar/",
    "/dashboard/polio/embeddedVaccineRepository/",
    "/dashboard/polio/embeddedVaccineStock/",
    "/dashboard/polio/embeddedLqasCountry/",
    "/dashboard/polio/embeddedLqasMap/",
]


class EmbeddedPageXFrameOptionsTestCase(TestCase):
    """Polio embed routes stay public and frameable when auth is enforced."""

    @override_settings(AUTHENTICATION_ENFORCED=True)
    def test_embedded_pages_are_public_and_frameable(self):
        # Avoid rendering iaso/index.html (needs webpack-stats.json in CI).
        with mock.patch(
            "hat.dashboard.views._base_iaso",
            return_value=HttpResponse("ok"),
        ):
            for path in EMBEDDED_PATHS:
                response = self.client.get(path)
                self.assertEqual(response.status_code, status.HTTP_200_OK, path)
                self.assertIsNone(response.get("X-Frame-Options"), path)
