from django.db import transaction

from catalog.models import Product, StockAdjustment
from common.exceptions import BusinessError, InsufficientStock, InvalidTransition

from .models import ALLOWED_TRANSITIONS, Order, OrderHistory, OrderStatus


def _lock_order(order_id):
    return Order.objects.select_for_update().get(pk=order_id)


def _lock_products(product_ids):
    products = Product.objects.select_for_update().filter(pk__in=product_ids).order_by("pk")
    return {p.pk: p for p in products}


def _record(order, action, from_status, to_status, user):
    OrderHistory.objects.create(
        order=order, action=action, from_status=from_status,
        to_status=to_status, performed_by=user,
    )


def _check_transition(order, target):
    if target not in ALLOWED_TRANSITIONS[order.status]:
        raise InvalidTransition(order.status, target)


def _change_status(order, target, action, user):
    previous = order.status
    order.status = target
    order.save(update_fields=["status", "updated_at"])
    _record(order, action, previous, target, user)


@transaction.atomic
def confirm_order(order_id, user):
    order = _lock_order(order_id)
    if order.status == OrderStatus.CONFIRMED:
        return order
    _check_transition(order, OrderStatus.CONFIRMED)

    items = list(order.items.all())
    products = _lock_products(sorted(i.product_id for i in items))

    shortages = [
        {
            "product": products[i.product_id].sku,
            "requested": i.quantity,
            "available": products[i.product_id].stock_quantity,
        }
        for i in items
        if products[i.product_id].stock_quantity < i.quantity
    ]
    if shortages:
        raise InsufficientStock(shortages)

    for i in items:
        product = products[i.product_id]
        product.stock_quantity -= i.quantity
        product.save(update_fields=["stock_quantity", "updated_at"])

    _change_status(order, OrderStatus.CONFIRMED, "confirmed", user)
    return order


@transaction.atomic
def cancel_order(order_id, user):
    order = _lock_order(order_id)
    if order.status == OrderStatus.CANCELLED:
        return order
    _check_transition(order, OrderStatus.CANCELLED)

    if order.status == OrderStatus.CONFIRMED:
        items = list(order.items.all())
        products = _lock_products(sorted(i.product_id for i in items))
        for i in items:
            product = products[i.product_id]
            product.stock_quantity += i.quantity
            product.save(update_fields=["stock_quantity", "updated_at"])

    _change_status(order, OrderStatus.CANCELLED, "cancelled", user)
    return order


@transaction.atomic
def ship_order(order_id, user):
    order = _lock_order(order_id)
    if order.status == OrderStatus.SHIPPED:
        return order
    _check_transition(order, OrderStatus.SHIPPED)
    _change_status(order, OrderStatus.SHIPPED, "shipped", user)
    return order


@transaction.atomic
def deliver_order(order_id, user):
    order = _lock_order(order_id)
    if order.status == OrderStatus.DELIVERED:
        return order
    _check_transition(order, OrderStatus.DELIVERED)
    _change_status(order, OrderStatus.DELIVERED, "delivered", user)
    return order


@transaction.atomic
def adjust_stock(product_id, change_quantity, reason, user):
    product = Product.objects.select_for_update().get(pk=product_id)
    new_quantity = product.stock_quantity + change_quantity
    if new_quantity < 0:
        raise BusinessError(
            code="invalid_stock_adjustment",
            message="Adjustment would make stock negative.",
            details=[{
                "product": product.sku,
                "current": product.stock_quantity,
                "change": change_quantity,
            }],
        )
    adjustment = StockAdjustment.objects.create(
        product=product, previous_quantity=product.stock_quantity,
        change_quantity=change_quantity, new_quantity=new_quantity,
        reason=reason, changed_by=user,
    )
    product.stock_quantity = new_quantity
    product.save(update_fields=["stock_quantity", "updated_at"])
    return adjustment