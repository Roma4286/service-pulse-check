import pytest
from flask_jwt_extended import decode_token

from tests.api.api_factories import create_user
from app.models import User


def login(client, username: str, password: str):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def get_access_cookie(app, client):
    return client.get_cookie(app.config["JWT_ACCESS_COOKIE_NAME"], path=app.config["JWT_ACCESS_COOKIE_PATH"])


def test_register_creates_user(client, session):
    response = client.post("/api/auth/register", json={"username": "alice", "password": "secret"})

    assert response.status_code == 201
    assert response.get_json() == {"success": True, "message": None, "data": {"username": "alice"}}
    stored_user = session.query(User).filter_by(username="alice").one()
    assert stored_user.check_password("secret")


def test_register_with_taken_username_returns_409(client, session):
    create_user(session, username="alice")

    response = client.post("/api/auth/register", json={"username": "alice", "password": "other"})

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
    assert response.get_json() == {"success": True, "message": None, "data": {"username": "alice"}}
    cookie = get_access_cookie(app, client)
    assert cookie is not None
    with app.app_context():
        assert decode_token(cookie.value)["sub"] == str(user.id)


def test_login_cookie_is_http_only_secure_and_scoped_to_api(client, session):
    create_user(session, username="alice", password="secret")

    response = login(client, "alice", "secret")

    set_cookies = [h for h in response.headers.getlist("Set-Cookie") if h.startswith("access_token_cookie=")]
    assert len(set_cookies) == 1
    set_cookie = set_cookies[0]

    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=Lax" in set_cookie
    assert "Path=/api/" in set_cookie


def test_login_cookie_gives_access_to_protected_endpoints(client, session):
    create_user(session, username="alice", password="secret")
    login(client, "alice", "secret")

    response = client.get("/api/services")

    assert response.status_code == 200


def test_login_with_wrong_password_returns_401(app, client, session):
    create_user(session, username="alice", password="secret")

    response = login(client, "alice", "wrong")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized", "message": "Invalid username or password"}
    assert get_access_cookie(app, client) is None


def test_login_with_unknown_user_returns_401(app, client):
    response = login(client, "nobody", "secret")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized", "message": "Invalid username or password"}
    assert get_access_cookie(app, client) is None


def test_logout_removes_cookie_and_access(app, client, session):
    create_user(session, username="alice", password="secret")
    login(client, "alice", "secret")

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.get_json() == {"success": True, "message": "Logged out", "data": None}
    assert get_access_cookie(app, client) is None
    assert client.get("/api/services").status_code == 401


def test_logout_without_login_returns_200(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
