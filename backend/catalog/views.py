from django.shortcuts import render

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import (
    ADMIN, INVENTORY, IsAdmin, IsAdminOrInventory, IsAnyStaffRole, user_roles,
)
from orders import services

from .models import Product
from .serializers import (
    ProductSerializer, StockAdjustmentInputSerializer, StockAdjustmentSerializer,
)


class ProductViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ["is_active", "category"]
    search_fields = ["name", "sku"]
    ordering_fields = ["name", "sku", "unit_price", "stock_quantity", "created_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "deactivate"):
            classes = [IsAdmin]
        elif self.action == "adjust_stock":
            classes = [IsAdminOrInventory]
        else:
            classes = [IsAnyStaffRole]
        return [cls() for cls in classes]

    def get_queryset(self):
        qs = super().get_queryset()
        roles = user_roles(self.request.user)
        if ADMIN in roles or INVENTORY in roles:
            return qs
        return qs.filter(is_active=True)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        product = self.get_object()
        if product.is_active:
            product.is_active = False
            product.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(product).data)

    @action(detail=True, methods=["post"], url_path="adjust-stock")
    def adjust_stock(self, request, pk=None):
        product = self.get_object()
        data = StockAdjustmentInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        adjustment = services.adjust_stock(
            product.pk, data.validated_data["change_quantity"],
            data.validated_data["reason"], request.user,
        )
        return Response(StockAdjustmentSerializer(adjustment).data, status=201)