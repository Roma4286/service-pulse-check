import pytest

from app.models import CheckResult, Service, ServiceType
from test.api.api_factories import create_check_result, create_service, create_user

SERVICES_URL = "/api/services"


def service_payload(**overrides) -> dict:
    payload = {
        "name": "api",
        "url": "https://api.example.com",
        "type": "http",
        "is_active": True,
        "interval_in_seconds": 30,
        "timeout_in_seconds": 2.5,
    }
    payload.update(overrides)
    return payload


def get_stored_service(session, service_id: int) -> Service | None:
    session.expunge_all()
    return session.get(Service, service_id)


# auth

PROTECTED_ENDPOINTS = [
    ("GET", SERVICES_URL),
    ("POST", SERVICES_URL),
    ("GET", f"{SERVICES_URL}/1"),
    ("PATCH", f"{SERVICES_URL}/1"),
    ("DELETE", f"{SERVICES_URL}/1"),
    ("GET", f"{SERVICES_URL}/1/results"),
    ("DELETE", f"{SERVICES_URL}/1/results"),
    ("DELETE", f"{SERVICES_URL}/1/results/1"),
]


@pytest.mark.parametrize(("method", "url"), PROTECTED_ENDPOINTS)
def test_protected_endpoint_without_token_returns_401(client, method, url):
    response = client.open(url, method=method)

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


@pytest.mark.parametrize(("method", "url"), PROTECTED_ENDPOINTS)
def test_protected_endpoint_with_invalid_token_returns_401(app, client, method, url):
    client.set_cookie(app.config["JWT_ACCESS_COOKIE_NAME"], "not-a-jwt", path=app.config["JWT_ACCESS_COOKIE_PATH"])

    response = client.open(url, method=method)

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


# GET /services


def test_get_services_returns_only_own_services(client, session, logged_in):
    service = create_service(session, logged_in)
    create_service(session, create_user(session))

    response = client.get(SERVICES_URL)

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert [item["id"] for item in body["data"]["services"]] == [service.id]


@pytest.mark.parametrize("is_active", [True, False])
def test_get_services_filters_by_is_active(client, session, logged_in, is_active):
    active_service = create_service(session, logged_in, is_active=True)
    inactive_service = create_service(session, logged_in, is_active=False)
    expected_service = active_service if is_active else inactive_service

    response = client.get(SERVICES_URL, query_string={"is_active": str(is_active).lower()})

    assert response.status_code == 200
    assert [item["id"] for item in response.get_json()["data"]["services"]] == [expected_service.id]


@pytest.mark.usefixtures("logged_in")
def test_get_services_returns_empty_list(client):
    response = client.get(SERVICES_URL)

    assert response.status_code == 200
    assert response.get_json()["data"] == {"services": []}


# GET /services/<id>


def test_get_service_returns_service(client, session, logged_in):
    service = create_service(
        session, logged_in, name="demo", url="https://example.com", interval_in_seconds=60, timeout_in_seconds=5.0
    )

    response = client.get(f"{SERVICES_URL}/{service.id}")

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "message": None,
        "data": {
            "id": service.id,
            "name": "demo",
            "url": "https://example.com",
            "type": "http",
            "is_active": True,
            "interval_in_seconds": 60,
            "timeout_in_seconds": 5.0,
        },
    }


@pytest.mark.usefixtures("logged_in")
def test_get_service_returns_404_when_missing(client):
    response = client.get(f"{SERVICES_URL}/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Not Found"


@pytest.mark.usefixtures("logged_in")
def test_get_service_returns_404_for_foreign_service(client, session):
    foreign_service = create_service(session, create_user(session))

    response = client.get(f"{SERVICES_URL}/{foreign_service.id}")

    assert response.status_code == 404


# POST /services


def test_create_service_returns_201_and_schedules(client, session, scheduler, logged_in):
    response = client.post(SERVICES_URL, json=service_payload())

    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["name"] == "api"
    assert data["type"] == "http"
    assert data["interval_in_seconds"] == 30
    assert data["timeout_in_seconds"] == 2.5

    stored_service = get_stored_service(session, data["id"])
    assert stored_service is not None
    assert stored_service.user_id == logged_in.id
    scheduler.create_task.assert_called_once_with(
        service_id=data["id"],
        url=stored_service.url,
        service_type=ServiceType.HTTP,
        interval_in_seconds=30,
        timeout_in_seconds=2.5,
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"url": "not-a-url"},
        {"type": "ftp"},
        {"interval_in_seconds": 0},
        {"timeout_in_seconds": -1},
        {"interval_in_seconds": 10, "timeout_in_seconds": 20.0},
        {"name": None},
    ],
    ids=["bad-url", "bad-type", "zero-interval", "negative-timeout", "timeout-above-interval", "no-name"],
)
@pytest.mark.usefixtures("logged_in")
def test_create_service_with_invalid_body_returns_400(client, session, scheduler, overrides):
    response = client.post(SERVICES_URL, json=service_payload(**overrides))

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert session.query(Service).count() == 0
    scheduler.create_task.assert_not_called()


@pytest.mark.usefixtures("logged_in")
def test_create_service_returns_500_when_scheduling_fails(client, session, scheduler):
    scheduler.create_task.side_effect = RuntimeError("redis is down")

    response = client.post(SERVICES_URL, json=service_payload())

    assert response.status_code == 500
    assert response.get_json()["error"] == "Internal Server Error"
    assert session.query(Service).count() == 0


# PATCH /services/<id>


def test_update_service_returns_updated_service(client, session, logged_in):
    service = create_service(session, logged_in, name="old")

    response = client.patch(f"{SERVICES_URL}/{service.id}", json={"name": "renamed"})

    assert response.status_code == 200
    assert response.get_json()["data"]["name"] == "renamed"
    assert get_stored_service(session, service.id).name == "renamed"


def test_update_service_deactivation_deletes_task(client, session, scheduler, logged_in):
    service = create_service(session, logged_in, is_active=True)

    response = client.patch(f"{SERVICES_URL}/{service.id}", json={"is_active": False})

    assert response.status_code == 200
    assert get_stored_service(session, service.id).is_active is False
    scheduler.delete_task.assert_called_once_with(service.id)


def test_update_service_with_timeout_above_current_interval_returns_400(client, session, logged_in):
    service = create_service(session, logged_in, interval_in_seconds=60, timeout_in_seconds=5.0)

    response = client.patch(f"{SERVICES_URL}/{service.id}", json={"timeout_in_seconds": 61.0})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert get_stored_service(session, service.id).timeout_in_seconds == 5.0


def test_update_service_with_invalid_body_returns_400(client, session, logged_in):
    service = create_service(session, logged_in)

    response = client.patch(f"{SERVICES_URL}/{service.id}", json={"interval_in_seconds": 0})

    assert response.status_code == 400


@pytest.mark.usefixtures("logged_in")
def test_update_service_returns_404_for_foreign_service(client, session):
    foreign_service = create_service(session, create_user(session), name="foreign")

    response = client.patch(f"{SERVICES_URL}/{foreign_service.id}", json={"name": "hacked"})

    assert response.status_code == 404
    assert get_stored_service(session, foreign_service.id).name == "foreign"


# DELETE /services/<id>


def test_delete_service_returns_204(client, session, scheduler, logged_in):
    service = create_service(session, logged_in)

    response = client.delete(f"{SERVICES_URL}/{service.id}")

    assert response.status_code == 204
    assert get_stored_service(session, service.id) is None
    scheduler.delete_task.assert_called_once_with(service.id)


@pytest.mark.usefixtures("logged_in")
def test_delete_service_returns_404_for_foreign_service(client, session, scheduler):
    foreign_service = create_service(session, create_user(session))

    response = client.delete(f"{SERVICES_URL}/{foreign_service.id}")

    assert response.status_code == 404
    assert get_stored_service(session, foreign_service.id) is not None
    scheduler.delete_task.assert_not_called()


# /services/<id>/results


def test_get_service_results_returns_results(client, session, logged_in):
    service = create_service(session, logged_in)
    result = create_check_result(session, service, response_time=0.25)

    response = client.get(f"{SERVICES_URL}/{service.id}/results")

    assert response.status_code == 200
    [item] = response.get_json()["data"]["results"]
    assert item["id"] == result.id
    assert item["service_id"] == service.id
    assert item["status"] == "success"
    assert item["response_time"] == 0.25
    assert item["created_at"] is not None


@pytest.mark.usefixtures("logged_in")
def test_get_service_results_returns_404_for_foreign_service(client, session):
    foreign_service = create_service(session, create_user(session))
    create_check_result(session, foreign_service)

    response = client.get(f"{SERVICES_URL}/{foreign_service.id}/results")

    assert response.status_code == 404


def test_delete_service_result_returns_204(client, session, logged_in):
    service = create_service(session, logged_in)
    result = create_check_result(session, service)
    other_result = create_check_result(session, service)

    response = client.delete(f"{SERVICES_URL}/{service.id}/results/{result.id}")

    assert response.status_code == 204
    assert [row.id for row in session.query(CheckResult).all()] == [other_result.id]


def test_delete_service_result_returns_404_when_missing(client, session, logged_in):
    service = create_service(session, logged_in)

    response = client.delete(f"{SERVICES_URL}/{service.id}/results/999")

    assert response.status_code == 404


@pytest.mark.usefixtures("logged_in")
def test_delete_service_result_returns_404_for_foreign_service(client, session):
    foreign_service = create_service(session, create_user(session))
    result = create_check_result(session, foreign_service)

    response = client.delete(f"{SERVICES_URL}/{foreign_service.id}/results/{result.id}")

    assert response.status_code == 404
    assert session.query(CheckResult).count() == 1


def test_delete_service_results_returns_204(client, session, logged_in):
    service = create_service(session, logged_in)
    foreign_service = create_service(session, create_user(session))
    create_check_result(session, service)
    create_check_result(session, service)
    foreign_result = create_check_result(session, foreign_service)

    response = client.delete(f"{SERVICES_URL}/{service.id}/results")

    assert response.status_code == 204
    assert [row.id for row in session.query(CheckResult).all()] == [foreign_result.id]


@pytest.mark.usefixtures("logged_in")
def test_delete_service_results_returns_404_for_foreign_service(client, session):
    foreign_service = create_service(session, create_user(session))
    create_check_result(session, foreign_service)

    response = client.delete(f"{SERVICES_URL}/{foreign_service.id}/results")

    assert response.status_code == 404
    assert session.query(CheckResult).count() == 1
