from unittest import mock

from django.http import HttpResponse
from rest_framework import status

from iaso.test import TestCase


class EmbeddedPageXFrameOptionsTestCase(TestCase):
    """Polio embed routes serve the SPA shell and must be frameable."""

    def test_embedded_calendar_is_exempt(self):
        # Avoid rendering iaso/index.html (needs webpack-stats.json in CI).
        with mock.patch(
            "hat.dashboard.views._base_iaso",
            return_value=HttpResponse("ok"),
        ):
            response = self.client.get("/polio/polio/embeddedCalendar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.get("X-Frame-Options"))
