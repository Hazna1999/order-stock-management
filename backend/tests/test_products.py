import pytest

URL = "/api/v1/products/"


def payload(**overrides):
    data = {"name": "Widget", "sku": "W-1", "unit_price": "10.00", "stock_quantity": 5}
    data.update(overrides)
    return data


def test_unauthenticated_gets_401(anon_client):
    assert anon_client.get(URL).status_code == 401


def test_sku_unique_case_insensitive(admin_client, product):
    response = admin_client.post(URL, payload(sku="w-1"), format="json")
    assert response.status_code == 400
    assert "sku" in response.data["details"]


def test_sku_is_trimmed(admin_client):
    response = admin_client.post(URL, payload(sku="  AB-1  ", name="  Bolt "), format="json")
    assert response.status_code == 201
    assert response.data["sku"] == "AB-1"
    assert response.data["name"] == "Bolt"


@pytest.mark.parametrize("price", ["0", "0.00", "-5", "10.123", "abc"])
def test_invalid_price_rejected(admin_client, price):
    response = admin_client.post(URL, payload(unit_price=price), format="json")
    assert response.status_code == 400
    assert "unit_price" in response.data["details"]


@pytest.mark.parametrize("field", ["stock_quantity", "reorder_level"])
@pytest.mark.parametrize("value", [-1, 1.5])
def test_invalid_quantities_rejected(admin_client, field, value):
    response = admin_client.post(URL, payload(**{field: value}), format="json")
    assert response.status_code == 400


@pytest.mark.parametrize("field", ["name", "sku"])
def test_blank_required_fields_rejected(admin_client, field):
    response = admin_client.post(URL, payload(**{field: "   "}), format="json")
    assert response.status_code == 400


def test_stock_cannot_be_edited_directly(admin_client, product):
    response = admin_client.patch(f"{URL}{product.id}/", {"stock_quantity": 99}, format="json")
    assert response.status_code == 400


def test_sales_cannot_create_product(sales_client):
    assert sales_client.post(URL, payload(), format="json").status_code == 403


def test_sales_sees_only_active_products(sales_client, admin_client, product):
    admin_client.post(f"{URL}{product.id}/deactivate/")
    assert sales_client.get(URL).data["count"] == 0
    assert admin_client.get(URL).data["count"] == 1


def test_deactivate_is_idempotent(admin_client, product):
    first = admin_client.post(f"{URL}{product.id}/deactivate/")
    second = admin_client.post(f"{URL}{product.id}/deactivate/")
    assert first.status_code == second.status_code == 200
    assert second.data["is_active"] is False


def test_search_partial_case_insensitive(admin_client, product):
    assert admin_client.get(URL, {"search": "wid"}).data["count"] == 1
    assert admin_client.get(URL, {"search": "w-"}).data["count"] == 1
    assert admin_client.get(URL, {"search": "zzz"}).data["count"] == 0


def test_filter_by_active_and_category(admin_client, product):
    admin_client.post(URL, payload(sku="T-1", category="Tools"), format="json")
    assert admin_client.get(URL, {"category": "Tools"}).data["count"] == 1
    assert admin_client.get(URL, {"is_active": "false"}).data["count"] == 0


def test_adjust_stock(inventory_client, product):
    response = inventory_client.post(
        f"{URL}{product.id}/adjust-stock/",
        {"change_quantity": -2, "reason": "Damaged"}, format="json",
    )
    assert response.status_code == 201
    product.refresh_from_db()
    assert product.stock_quantity == 3
    assert response.data["previous_quantity"] == 5
    assert response.data["new_quantity"] == 3


def test_adjust_stock_cannot_go_negative(inventory_client, product):
    response = inventory_client.post(
        f"{URL}{product.id}/adjust-stock/",
        {"change_quantity": -6, "reason": "Oops"}, format="json",
    )
    assert response.status_code == 409
    assert response.data["code"] == "invalid_stock_adjustment"
    product.refresh_from_db()
    assert product.stock_quantity == 5


def test_adjust_stock_requires_reason(inventory_client, product):
    response = inventory_client.post(
        f"{URL}{product.id}/adjust-stock/",
        {"change_quantity": 1, "reason": "  "}, format="json",
    )
    assert response.status_code == 400


def test_sales_cannot_adjust_stock(sales_client, product):
    response = sales_client.post(
        f"{URL}{product.id}/adjust-stock/",
        {"change_quantity": 1, "reason": "x"}, format="json",
    )
    assert response.status_code == 403

def test_low_stock_report(admin_client, product):
    admin_client.post(URL, payload(sku="L-1", stock_quantity=2, reorder_level=5), format="json")
    response = admin_client.get(f"{URL}low-stock/")
    assert response.status_code == 200
    assert [p["sku"] for p in response.data["results"]] == ["L-1"]