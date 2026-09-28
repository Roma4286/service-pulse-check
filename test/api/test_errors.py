import pytest

from app.repositories.service_repository import ServiceRepository


@pytest.mark.usefixtures("logged_in")
def test_malformed_json_body_returns_400_in_api_format(client):
    response = client.post("/api/services", data="{not json", content_type="application/json")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"


@pytest.mark.usefixtures("logged_in")
def test_unexpected_error_returns_500_without_details(client, monkeypatch):
    def broken_get_services(self, user_id, is_active=None):
        raise RuntimeError("secret internal details")

    monkeypatch.setattr(ServiceRepository, "get_services", broken_get_services)

    response = client.get("/api/services")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal Server Error", "message": "Internal server error"}
