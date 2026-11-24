import django_filters

from .models import Order


class OrderFilter(django_filters.FilterSet):
    product = django_filters.NumberFilter(field_name="items__product", distinct=True)
    date_from = django_filters.DateFilter(field_name="order_date", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="order_date", lookup_expr="date__lte")

    class Meta:
        model = Order
        fields = ["status", "customer"]