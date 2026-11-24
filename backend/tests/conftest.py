import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from catalog.models import Product
from common.permissions import ADMIN, INVENTORY, SALES
from customers.models import Customer


def make_user(username, role):
    user = User.objects.create_user(username, password="Pass@1234")
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin(db):
    return make_user("admin", ADMIN)


@pytest.fixture
def sales(db):
    return make_user("sales", SALES)


@pytest.fixture
def sales_other(db):
    return make_user("sales_other", SALES)


@pytest.fixture
def inventory(db):
    return make_user("inventory", INVENTORY)


@pytest.fixture
def admin_client(admin):
    return client_for(admin)


@pytest.fixture
def sales_client(sales):
    return client_for(sales)


@pytest.fixture
def sales_other_client(sales_other):
    return client_for(sales_other)


@pytest.fixture
def inventory_client(inventory):
    return client_for(inventory)


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Widget", sku="W-1", unit_price="10.00", stock_quantity=5
    )


@pytest.fixture
def customer(db):
    return Customer.objects.create(name="Acme", email="a@acme.com")