from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from catalog.models import Product
from customers.models import Customer

from .models import Order, OrderHistory, OrderItem, OrderStatus


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)

    def validate_product(self, product):
        if not product.is_active:
            raise serializers.ValidationError(f"Product {product.sku} is inactive.")
        return product


class OrderItemSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_sku", "product_name", "quantity", "unit_price", "line_total"]
        read_only_fields = fields


class OrderHistorySerializer(serializers.ModelSerializer):
    performed_by = serializers.StringRelatedField()

    class Meta:
        model = OrderHistory
        fields = ["id", "action", "from_status", "to_status", "performed_by", "performed_at"]


class OrderSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    items = OrderItemInputSerializer(many=True, write_only=True)
    lines = OrderItemSerializer(source="items", many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "customer", "customer_name", "order_date",
            "status", "total_amount", "created_by", "created_at", "updated_at",
            "items", "lines",
        ]
        read_only_fields = [
            "id", "order_number", "order_date", "status", "total_amount",
            "created_by", "created_at", "updated_at",
        ]

    def validate_customer(self, customer):
        if not customer.is_active:
            raise serializers.ValidationError("Customer is inactive.")
        return customer

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("An order needs at least one item.")
        ids = [i["product"].pk for i in items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("A product may appear only once in an order.")
        return items

    def _build_items(self, order, items):
        total = Decimal("0.00")
        rows = []
        for item in items:
            product = item["product"]
            line_total = product.unit_price * item["quantity"]
            total += line_total
            rows.append(OrderItem(
                order=order, product=product, quantity=item["quantity"],
                unit_price=product.unit_price, line_total=line_total,
            ))
        OrderItem.objects.bulk_create(rows)
        order.total_amount = total
        order.save(update_fields=["total_amount", "updated_at"])

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        user = self.context["request"].user
        order = Order.objects.create(created_by=user, **validated_data)
        self._build_items(order, items)
        OrderHistory.objects.create(
            order=order, action="created", from_status="",
            to_status=OrderStatus.DRAFT, performed_by=user,
        )
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        from common.exceptions import OrderNotEditable
        if instance.status != OrderStatus.DRAFT:
            raise OrderNotEditable()
        items = validated_data.pop("items", None)
        if "customer" in validated_data:
            instance.customer = validated_data["customer"]
            instance.save(update_fields=["customer", "updated_at"])
        if items is not None:
            instance.items.all().delete()
            self._build_items(instance, items)
        return instance