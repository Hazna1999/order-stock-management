import pytest

ORDERS = "/api/v1/orders/"


def new_order(client, customer, product, qty=1):
    body = {"customer": customer.id, "items": [{"product": product.id, "quantity": qty}]}
    return client.post(ORDERS, body, format="json").data["id"]


def test_inventory_cannot_create_order(inventory_client, customer, product):
    body = {"customer": customer.id, "items": [{"product": product.id, "quantity": 1}]}
    assert inventory_client.post(ORDERS, body, format="json").status_code == 403


def test_sales_cannot_confirm_someone_elses_order_404(sales_client, sales_other_client, customer, product):
    order_id = new_order(sales_other_client, customer, product)
    assert sales_client.post(f"{ORDERS}{order_id}/confirm/").status_code == 404


def test_sales_sees_only_own_orders(sales_client, sales_other_client, customer, product):
    new_order(sales_other_client, customer, product)
    assert sales_client.get(ORDERS).data["count"] == 0
    assert sales_other_client.get(ORDERS).data["count"] == 1


def test_inventory_and_admin_see_all_orders(sales_client, inventory_client, admin_client, customer, product):
    new_order(sales_client, customer, product)
    assert inventory_client.get(ORDERS).data["count"] == 1
    assert admin_client.get(ORDERS).data["count"] == 1


def test_inventory_cannot_confirm(sales_client, inventory_client, customer, product):
    order_id = new_order(sales_client, customer, product)
    assert inventory_client.post(f"{ORDERS}{order_id}/confirm/").status_code == 403


def test_sales_cannot_ship(sales_client, customer, product):
    order_id = new_order(sales_client, customer, product)
    sales_client.post(f"{ORDERS}{order_id}/confirm/")
    assert sales_client.post(f"{ORDERS}{order_id}/ship/").status_code == 403


def test_inventory_can_ship_but_not_deliver(sales_client, inventory_client, customer, product):
    order_id = new_order(sales_client, customer, product)
    sales_client.post(f"{ORDERS}{order_id}/confirm/")
    assert inventory_client.post(f"{ORDERS}{order_id}/ship/").status_code == 200
    assert inventory_client.post(f"{ORDERS}{order_id}/deliver/").status_code == 403


def test_inventory_cannot_cancel(sales_client, inventory_client, customer, product):
    order_id = new_order(sales_client, customer, product)
    assert inventory_client.post(f"{ORDERS}{order_id}/cancel/").status_code == 403


def test_admin_can_cancel_any_order(sales_client, admin_client, customer, product):
    order_id = new_order(sales_client, customer, product)
    assert admin_client.post(f"{ORDERS}{order_id}/cancel/").status_code == 200


def test_user_without_role_gets_403(db, customer):
    from django.contrib.auth.models import User
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(User.objects.create_user("norole", password="x"))
    assert client.get("/api/v1/products/").status_code == 403