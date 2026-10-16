import django_filters

from plugins.polio.models import DestructionReport, IncidentReport, OutgoingStockMovement


class OutgoingStockMovementFilter(django_filters.rest_framework.FilterSet):
    status = django_filters.ChoiceFilter(choices=OutgoingStockMovement.StatusChoices.choices)
    doses_per_vial = django_filters.NumberFilter()
    round_number = django_filters.NumberFilter(field_name="round__number")
    form_a_reception_date_from = django_filters.DateFilter(field_name="form_a_reception_date", lookup_expr="gte")
    form_a_reception_date_to = django_filters.DateFilter(field_name="form_a_reception_date", lookup_expr="lte")
    report_date_from = django_filters.DateFilter(field_name="report_date", lookup_expr="gte")
    report_date_to = django_filters.DateFilter(field_name="report_date", lookup_expr="lte")

    class Meta:
        model = OutgoingStockMovement
        fields: list = []


class DestructionReportFilter(django_filters.rest_framework.FilterSet):
    doses_per_vial = django_filters.NumberFilter()
    destruction_report_date_from = django_filters.DateFilter(field_name="destruction_report_date", lookup_expr="gte")
    destruction_report_date_to = django_filters.DateFilter(field_name="destruction_report_date", lookup_expr="lte")
    rrt_reception_date_from = django_filters.DateFilter(
        field_name="rrt_destruction_report_reception_date", lookup_expr="gte"
    )
    rrt_reception_date_to = django_filters.DateFilter(
        field_name="rrt_destruction_report_reception_date", lookup_expr="lte"
    )

    class Meta:
        model = DestructionReport
        fields: list = []


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
