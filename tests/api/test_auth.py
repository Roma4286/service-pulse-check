from datetime import UTC, datetime

import pytest
from flask_jwt_extended import decode_token

from app.models import ResultStatus, User
from tests.factories import create_check_result, create_service, create_user


def login(client, username: str, password: str):
    return client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )


def get_access_cookie(app, client):
    return client.get_cookie(
        app.config["JWT_ACCESS_COOKIE_NAME"], path=app.config["JWT_ACCESS_COOKIE_PATH"]
    )


def test_register_creates_user(client, session):
    response = client.post(
        "/api/auth/register", json={"username": "alice", "password": "secret"}
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "success": True,
        "message": None,
        "data": {"username": "alice"},
    }
    stored_user = session.query(User).filter_by(username="alice").one()
    assert stored_user.check_password("secret")


def test_register_with_taken_username_returns_409(client, session):
    create_user(session, username="alice")

    response = client.post(
        "/api/auth/register", json={"username": "alice", "password": "other"}
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "Conflict"
    assert session.query(User).count() == 1


@pytest.mark.parametrize(
    "body",
    [{"username": "alice"}, {"password": "secret"}, {}],
    ids=["no-password", "no-username", "empty"],
)
def test_register_with_invalid_body_returns_400(client, session, body):
    response = client.post("/api/auth/register", json=body)

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert session.query(User).count() == 0


def test_login_sets_access_token_cookie(app, client, session):
    user = create_user(session, username="alice", password="secret")

    response = login(client, "alice", "secret")

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "message": None,
        "data": {"username": "alice"},
    }
    cookie = get_access_cookie(app, client)
    assert cookie is not None
    with app.app_context():
        assert decode_token(cookie.value)["sub"] == str(user.id)


def test_login_cookie_is_http_only_secure_and_scoped_to_whole_site(client, session):
    create_user(session, username="alice", password="secret")

    response = login(client, "alice", "secret")

    set_cookies = [
        h
        for h in response.headers.getlist("Set-Cookie")
        if h.startswith("access_token_cookie=")
    ]
    assert len(set_cookies) == 1
    set_cookie = set_cookies[0]

    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=Lax" in set_cookie
    assert "Path=/;" in set_cookie


def test_login_cookie_gives_access_to_protected_endpoints(client, session):
    create_user(session, username="alice", password="secret")
    login(client, "alice", "secret")

    response = client.get("/api/services")

    assert response.status_code == 200


def test_login_sets_csrf_cookie_readable_by_js(client, session):
    create_user(session, username="alice", password="secret")

    response = login(client, "alice", "secret")

    set_cookies = [
        h
        for h in response.headers.getlist("Set-Cookie")
        if h.startswith("csrf_access_token=")
    ]
    assert len(set_cookies) == 1
    assert "HttpOnly" not in set_cookies[0]


def test_csrf_cookie_value_gives_access_to_unsafe_endpoints(app, client, session):
    create_user(session, username="alice", password="secret")
    login(client, "alice", "secret")
    csrf_cookie = client.get_cookie(
        app.config["JWT_ACCESS_CSRF_COOKIE_NAME"],
        path=app.config["JWT_ACCESS_CSRF_COOKIE_PATH"],
    )

    response = client.delete(
        "/api/services/999",
        headers={app.config["JWT_ACCESS_CSRF_HEADER_NAME"]: csrf_cookie.value},
    )

    assert response.status_code == 404


def test_login_with_wrong_password_returns_401(app, client, session):
    create_user(session, username="alice", password="secret")

    response = login(client, "alice", "wrong")

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "Unauthorized",
        "message": "Invalid username or password",
    }
    assert get_access_cookie(app, client) is None


def test_login_with_unknown_user_returns_401(app, client):
    response = login(client, "nobody", "secret")

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "Unauthorized",
        "message": "Invalid username or password",
    }
    assert get_access_cookie(app, client) is None


def test_logout_removes_cookie_and_access(app, client, session):
    create_user(session, username="alice", password="secret")
    login(client, "alice", "secret")

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "message": "Logged out",
        "data": None,
    }
    assert get_access_cookie(app, client) is None
    assert client.get("/api/services").status_code == 401


def test_logout_without_login_returns_200(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200


# GET /auth/me

ME_URL = "/api/auth/me"


def test_me_without_login_returns_401(client):
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


def test_me_returns_user_and_empty_home_data(client, logged_in):
    response = client.get(ME_URL)

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "message": None,
        "data": {
            "user": {"username": logged_in.username},
            "stats": {"services_total": 0, "services_active": 0},
            "services": [],
        },
    }


def test_me_returns_own_services_with_stats(client, session, logged_in):
    first = create_service(session, logged_in, name="first", is_active=True)
    second = create_service(session, logged_in, name="second", is_active=False)
    create_service(session, create_user(session), name="foreign")

    data = client.get(ME_URL).get_json()["data"]

    assert data["stats"] == {"services_total": 2, "services_active": 1}
    assert [service["id"] for service in data["services"]] == [first.id, second.id]
    assert data["services"][0] == {
        "id": first.id,
        "name": "first",
        "url": "https://example.com",
        "type": "http",
        "is_active": True,
        "interval_in_seconds": 60,
        "timeout_in_seconds": 5.0,
        "last_result": None,
    }


def test_me_returns_latest_check_result_of_each_service(client, session, logged_in):
    service = create_service(session, logged_in)
    create_check_result(
        session,
        service,
        status=ResultStatus.SUCCESS,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    latest = create_check_result(
        session,
        service,
        status=ResultStatus.FAIL,
        response_time=0.5,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    [service_data] = client.get(ME_URL).get_json()["data"]["services"]

    last_result = service_data["last_result"]
    assert last_result["id"] == latest.id
    assert last_result["service_id"] == service.id
    assert last_result["status"] == "fail"
    assert last_result["response_time"] == 0.5
    assert last_result["created_at"] is not None


def test_me_for_deleted_user_returns_401(client, session, logged_in):
    session.delete(logged_in)
    session.commit()

    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized", "message": "User not found"}
