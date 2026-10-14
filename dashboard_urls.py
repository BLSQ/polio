"""
Public Polio pages.

Included from hat/dashboard/urls.py, so these paths stay under /dashboard/.
"""

from django.urls import re_path

from hat.dashboard.views import embeddable_iaso


urlpatterns = [
    re_path(r"^polio/embeddedCalendar/.*$", embeddable_iaso, name="embedded_calendar"),
    re_path(r"^polio/embeddedVaccineRepository/.*$", embeddable_iaso, name="embedded_vaccine_repository"),
    re_path(r"^polio/embeddedVaccineStock/.*$", embeddable_iaso, name="embedded_vaccine_stock"),
    re_path(r"^polio/embeddedLqasCountry/.*$", embeddable_iaso, name="embedded_lqas_country"),
    re_path(r"^polio/embeddedLqasMap/.*$", embeddable_iaso, name="embedded_lqas_map"),
]
