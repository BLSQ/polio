import django_filters

from plugins.polio.models import OutgoingStockMovement


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
