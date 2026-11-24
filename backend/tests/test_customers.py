URL = "/api/v1/customers/"


def test_email_unique_case_insensitive(sales_client, customer):
    response = sales_client.post(URL, {"name": "Other", "email": "A@ACME.com"}, format="json")
    assert response.status_code == 400
    assert "email" in response.data["details"]


def test_invalid_email_rejected(sales_client):
    response = sales_client.post(URL, {"name": "X", "email": "not-an-email"}, format="json")
    assert response.status_code == 400


def test_name_required(sales_client):
    response = sales_client.post(URL, {"name": "  ", "email": "x@x.com"}, format="json")
    assert response.status_code == 400


def test_inventory_cannot_manage_customers(inventory_client):
    assert inventory_client.get(URL).status_code == 403


def test_update_own_email_is_allowed(sales_client, customer):
    response = sales_client.patch(f"{URL}{customer.id}/", {"email": "a@acme.com"}, format="json")
    assert response.status_code == 200


def test_deactivate_customer(sales_client, customer):
    response = sales_client.patch(f"{URL}{customer.id}/", {"is_active": False}, format="json")
    assert response.status_code == 200
    assert response.data["is_active"] is False