from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import (
    ADMIN, INVENTORY, SALES, IsAdmin, IsAdminOrInventory, IsAdminOrSales,
    IsAnyStaffRole, IsOrderOwnerOrAdmin, user_roles,
)

from . import services
from .filters import OrderFilter
from .models import Order
from .serializers import OrderHistorySerializer, OrderSerializer


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    search_fields = ["order_number", "customer__name", "customer__email"]
    ordering_fields = ["order_date", "total_amount", "created_at", "status"]

    def get_permissions(self):
        mapping = {
            "create": [IsAdminOrSales],
            "update": [IsAdminOrSales],
            "partial_update": [IsAdminOrSales],
            "confirm": [IsAdminOrSales],
            "cancel": [IsAdminOrSales, IsOrderOwnerOrAdmin],
            "ship": [IsAdminOrInventory],
            "deliver": [IsAdmin],
        }
        return [cls() for cls in mapping.get(self.action, [IsAnyStaffRole])]

    def get_queryset(self):
        qs = Order.objects.select_related("customer", "created_by").prefetch_related(
            "items__product"
        )
        roles = user_roles(self.request.user)
        if ADMIN in roles or INVENTORY in roles:
            return qs
        if SALES in roles:
            return qs.filter(created_by=self.request.user)
        return qs.none()

    def _transition(self, request, service):
        order = self.get_object()
        order = service(order.pk, request.user)
        return Response(OrderSerializer(order, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._transition(request, services.confirm_order)

    @action(detail=True, methods=["post"])
    def ship(self, request, pk=None):
        return self._transition(request, services.ship_order)

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        return self._transition(request, services.deliver_order)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(request, services.cancel_order)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        order = self.get_object()
        rows = order.history.select_related("performed_by")
        return Response(OrderHistorySerializer(rows, many=True).data)