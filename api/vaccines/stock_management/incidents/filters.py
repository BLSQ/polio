import django_filters

from plugins.polio.models import IncidentReport


class IncidentReportFilter(django_filters.rest_framework.FilterSet):
    stock_correction = django_filters.ChoiceFilter(choices=IncidentReport.StockCorrectionChoices.choices)
    doses_per_vial = django_filters.NumberFilter()
    date_of_incident_report_from = django_filters.DateFilter(field_name="date_of_incident_report", lookup_expr="gte")
    date_of_incident_report_to = django_filters.DateFilter(field_name="date_of_incident_report", lookup_expr="lte")
    rrt_reception_date_from = django_filters.DateFilter(field_name="incident_report_received_by_rrt", lookup_expr="gte")
    rrt_reception_date_to = django_filters.DateFilter(field_name="incident_report_received_by_rrt", lookup_expr="lte")

    class Meta:
        model = IncidentReport
        fields: list = []
