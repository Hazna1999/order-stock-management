from decimal import Decimal

from rest_framework import serializers

from .models import Product, StockAdjustment


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=200)
    sku = serializers.CharField(max_length=50)
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )

    class Meta:
        model = Product
        fields = [
            "id", "name", "sku", "description", "category", "unit_price",
            "stock_quantity", "reorder_level", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate_sku(self, value):
        value = value.strip()
        qs = Product.objects.filter(sku__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value

    def validate_name(self, value):
        return value.strip()

    def update(self, instance, validated_data):
        new_stock = validated_data.get("stock_quantity", instance.stock_quantity)
        if new_stock != instance.stock_quantity:
            raise serializers.ValidationError(
                {"stock_quantity": "Use the adjust-stock action to change stock."}
            )
        return super().update(instance, validated_data)
class StockAdjustmentInputSerializer(serializers.Serializer):
    change_quantity = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)

    def validate_change_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Change must not be zero.")
        return value

    def validate_reason(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("A reason is required.")
        return value


class StockAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustment
        fields = "__all__"
