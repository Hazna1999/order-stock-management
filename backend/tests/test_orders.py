from decimal import Decimal

import pytest

from catalog.models import Product
from orders.models import ALLOWED_TRANSITIONS, Order, OrderHistory, OrderStatus

ORDERS = "/api/v1/orders/"


def create_order(client, customer, product, quantity=2, **extra):
    body = {"customer": customer.id, "items": [{"product": product.id, "quantity": quantity}]}
    body.update(extra)
    return client.post(ORDERS, body, format="json")


def stock(product):
    product.refresh_from_db()
    return product.stock_quantity


# ---------- creation, snapshot, totals ----------

def test_create_order_is_draft_with_server_totals(sales_client, sales, customer, product):
    response = create_order(sales_client, customer, product, quantity=3)
    assert response.status_code == 201
    assert response.data["status"] == "DRAFT"
    assert response.data["total_amount"] == "30.00"
    assert response.data["created_by"] == sales.id
    assert response.data["order_number"].startswith("ORD-")
    assert response.data["lines"][0]["line_total"] == "30.00"


def test_client_supplied_totals_are_ignored(sales_client, customer, product):
    response = create_order(
        sales_client, customer, product, quantity=2,
        total_amount="1.00", status="CONFIRMED", created_by=999, order_number="HACK",
    )
    assert response.status_code == 201
    assert response.data["total_amount"] == "20.00"
    assert response.data["status"] == "DRAFT"
    assert response.data["order_number"] != "HACK"


def test_unit_price_is_a_snapshot(sales_client, admin_client, customer, product):
    order_id = create_order(sales_client, customer, product, quantity=2).data["id"]
    admin_client.patch(f"/api/v1/products/{product.id}/", {"unit_price": "99.00"}, format="json")
    detail = sales_client.get(f"{ORDERS}{order_id}/").data
    assert detail["lines"][0]["unit_price"] == "10.00"
    assert detail["total_amount"] == "20.00"


def test_duplicate_product_in_order_rejected(sales_client, customer, product):
    body = {"customer": customer.id, "items": [
        {"product": product.id, "quantity": 1}, {"product": product.id, "quantity": 1}]}
    assert sales_client.post(ORDERS, body, format="json").status_code == 400


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_must_be_at_least_one(sales_client, customer, product, quantity):
    assert create_order(sales_client, customer, product, quantity=quantity).status_code == 400


def test_inactive_product_rejected(sales_client, admin_client, customer, product):
    admin_client.post(f"/api/v1/products/{product.id}/deactivate/")
    assert create_order(sales_client, customer, product).status_code in (400, 404)


def test_inactive_customer_rejected(sales_client, customer, product):
    customer.is_active = False
    customer.save()
    assert create_order(sales_client, customer, product).status_code == 400


def test_unknown_customer_rejected(sales_client, customer, product):
    body = {"customer": 99999, "items": [{"product": product.id, "quantity": 1}]}
    assert sales_client.post(ORDERS, body, format="json").status_code == 400


# ---------- confirm, stock, idempotency ----------

def test_confirm_deducts_stock_once(sales_client, customer, product):
    order_id = create_order(sales_client, customer, product, quantity=4).data["id"]
    first = sales_client.post(f"{ORDERS}{order_id}/confirm/")
    second = sales_client.post(f"{ORDERS}{order_id}/confirm/")
    assert first.status_code == second.status_code == 200
    assert stock(product) == 1
    assert OrderHistory.objects.filter(order_id=order_id, action="confirmed").count() == 1


def test_insufficient_stock_names_every_short_product(sales_client, customer, product):
    other = Product.objects.create(name="Gadget", sku="G-1", unit_price="5.00", stock_quantity=1)
    body = {"customer": customer.id, "items": [
        {"product": product.id, "quantity": 9}, {"product": other.id, "quantity": 3}]}
    order_id = sales_client.post(ORDERS, body, format="json").data["id"]
    response = sales_client.post(f"{ORDERS}{order_id}/confirm/")
    assert response.status_code == 409
    assert response.data["code"] == "insufficient_stock"
    assert {d["product"] for d in response.data["details"]} == {"W-1", "G-1"}
    assert {"requested", "available"} <= set(response.data["details"][0])
    assert stock(product) == 5 and stock(other) == 1
    assert Order.objects.get(pk=order_id).status == OrderStatus.DRAFT
    assert OrderHistory.objects.filter(order_id=order_id).count() == 1  # only "created"


# ---------- cancel ----------

def test_cancel_confirmed_restores_stock_once(sales_client, customer, product):
    order_id = create_order(sales_client, customer, product, quantity=4).data["id"]
    sales_client.post(f"{ORDERS}{order_id}/confirm/")
    assert stock(product) == 1
    sales_client.post(f"{ORDERS}{order_id}/cancel/")
    sales_client.post(f"{ORDERS}{order_id}/cancel/")
    assert stock(product) == 5
    assert OrderHistory.objects.filter(order_id=order_id, action="cancelled").count() == 1


def test_cancel_draft_does_not_touch_stock(sales_client, customer, product):
    order_id = create_order(sales_client, customer, product, quantity=4).data["id"]
    assert sales_client.post(f"{ORDERS}{order_id}/cancel/").status_code == 200
    assert stock(product) == 5


# ---------- lifecycle: every invalid transition ----------

ALL = list(OrderStatus)
INVALID = [(a, b) for a in ALL for b in ALL if a != b and b not in ALLOWED_TRANSITIONS[a]]
ACTION_FOR = {
    OrderStatus.CONFIRMED: "confirm",
    OrderStatus.SHIPPED: "ship",
    OrderStatus.DELIVERED: "deliver",
    OrderStatus.CANCELLED: "cancel",
}


@pytest.mark.parametrize("current,target", [p for p in INVALID if p[1] in ACTION_FOR])
def test_invalid_transitions_rejected(admin_client, customer, product, current, target):
    order_id = create_order(admin_client, customer, product, quantity=1).data["id"]
    Order.objects.filter(pk=order_id).update(status=current)
    response = admin_client.post(f"{ORDERS}{order_id}/{ACTION_FOR[target]}/")
    assert response.status_code == 409
    assert response.data["code"] == "invalid_status_transition"
    assert Order.objects.get(pk=order_id).status == current
    assert OrderHistory.objects.filter(order_id=order_id).count() == 1


def test_full_happy_path_and_audit(sales_client, inventory_client, admin_client, customer, product):
    order_id = create_order(sales_client, customer, product, quantity=1).data["id"]
    sales_client.post(f"{ORDERS}{order_id}/confirm/")
    inventory_client.post(f"{ORDERS}{order_id}/ship/")
    admin_client.post(f"{ORDERS}{order_id}/deliver/")
    admin_client.post(f"{ORDERS}{order_id}/deliver/")  # repeat: no new row
    history = admin_client.get(f"{ORDERS}{order_id}/history/").data
    assert [h["action"] for h in history] == ["created", "confirmed", "shipped", "delivered"]
    assert history[0]["from_status"] == "" and history[0]["performed_by"]


# ---------- edit lock ----------

def test_draft_order_can_be_edited(sales_client, customer, product):
    order_id = create_order(sales_client, customer, product, quantity=1).data["id"]
    response = sales_client.patch(
        f"{ORDERS}{order_id}/", {"items": [{"product": product.id, "quantity": 5}]}, format="json")
    assert response.status_code == 200
    assert Order.objects.get(pk=order_id).total_amount == Decimal("50.00")


def test_confirmed_order_cannot_be_edited(sales_client, customer, product):
    order_id = create_order(sales_client, customer, product, quantity=1).data["id"]
    sales_client.post(f"{ORDERS}{order_id}/confirm/")
    response = sales_client.patch(
        f"{ORDERS}{order_id}/", {"items": [{"product": product.id, "quantity": 2}]}, format="json")
    assert response.status_code == 409
    assert response.data["code"] == "order_not_editable"
    assert Order.objects.get(pk=order_id).total_amount == Decimal("10.00")