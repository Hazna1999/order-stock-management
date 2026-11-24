import threading

import pytest
from django.contrib.auth.models import User
from django.db import connection

from catalog.models import Product
from common.exceptions import InsufficientStock
from customers.models import Customer
from orders import services
from orders.models import Order, OrderItem, OrderStatus


@pytest.mark.django_db(transaction=True)
def test_two_parallel_confirms_compete_for_last_units():
    user = User.objects.create_user("racer", password="x")
    customer = Customer.objects.create(name="Acme", email="a@acme.com")
    product = Product.objects.create(name="Widget", sku="W-1", unit_price="10.00", stock_quantity=5)

    order_ids = []
    for _ in range(2):
        order = Order.objects.create(customer=customer, created_by=user)
        OrderItem.objects.create(order=order, product=product, quantity=4,
                                 unit_price=product.unit_price, line_total=40)
        order_ids.append(order.id)

    barrier = threading.Barrier(2)
    results = []

    def worker(order_id):
        try:
            barrier.wait()
            services.confirm_order(order_id, user)
            results.append("ok")
        except InsufficientStock:
            results.append("insufficient")
        except Exception as exc:
            results.append(f"error: {exc!r}")
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(oid,)) for oid in order_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == ["insufficient", "ok"]
    product.refresh_from_db()
    assert product.stock_quantity == 1
    assert Order.objects.filter(status=OrderStatus.CONFIRMED).count() == 1


@pytest.mark.django_db(transaction=True)
def test_same_order_confirmed_in_parallel_deducts_once():
    user = User.objects.create_user("racer", password="x")
    customer = Customer.objects.create(name="Acme", email="a@acme.com")
    product = Product.objects.create(name="Widget", sku="W-1", unit_price="10.00", stock_quantity=10)
    order = Order.objects.create(customer=customer, created_by=user)
    OrderItem.objects.create(order=order, product=product, quantity=4,
                             unit_price=product.unit_price, line_total=40)

    barrier = threading.Barrier(2)
    errors = []

    def worker():
        try:
            barrier.wait()
            services.confirm_order(order.id, user)
        except Exception as exc:
            errors.append(repr(exc))
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    product.refresh_from_db()
    assert product.stock_quantity == 6  # deducted once, not twice