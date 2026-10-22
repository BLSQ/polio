import django_filters

from plugins.polio.models import DestructionReport


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
