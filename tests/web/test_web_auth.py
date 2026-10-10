import pytest
from flask_jwt_extended import decode_token

from app.models import User
from tests.factories import create_user


def register(
    client,
    username: str = "alice",
    password: str = "password123",
    confirm_password: str | None = None,
):
    return client.post(
        "/register",
        data={
            "username": username,
            "password": password,
            "confirm_password": password
            if confirm_password is None
            else confirm_password,
        },
    )


def login(client, username: str = "alice", password: str = "secret"):
    return client.post("/login", data={"username": username, "password": password})


def get_access_cookie(app, client):
    return client.get_cookie(
        app.config["JWT_ACCESS_COOKIE_NAME"], path=app.config["JWT_ACCESS_COOKIE_PATH"]
    )


# /register


def test_register_page_renders_form(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert b'action="/register"' in response.data


def test_register_creates_user_and_redirects_to_login(client, session):
    response = register(client)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    stored_user = session.query(User).filter_by(username="alice").one()
    assert stored_user.check_password("password123")


def test_register_strips_username(client, session):
    register(client, username="  alice  ")

    assert session.query(User).filter_by(username="alice").count() == 1


def test_register_with_mismatched_passwords_shows_error(client, session):
    response = register(
        client, password="password123", confirm_password="other-password"
    )

    assert response.status_code == 400
    assert b"Passwords do not match" in response.data
    assert b'value="alice"' in response.data
    assert session.query(User).count() == 0


@pytest.mark.parametrize(
    ("form", "error"),
    [
        ({"username": "al"}, b"Username must be 3-255 characters"),
        ({"username": "a" * 256}, b"Username must be 3-255 characters"),
        ({"password": "short12"}, b"Password must be at least 8 characters"),
    ],
    ids=["username-too-short", "username-too-long", "password-too-short"],
)
def test_register_with_invalid_length_shows_error(client, session, form, error):
    response = register(client, **form)

    assert response.status_code == 400
    assert error in response.data
    assert session.query(User).count() == 0


def test_register_with_empty_fields_shows_error(client, session):
    response = register(client, username="  ", password="")

    assert response.status_code == 400
    assert b"Username and password are required" in response.data
    assert session.query(User).count() == 0


def test_register_with_taken_username_shows_error(client, session):
    create_user(session, username="alice")

    response = register(client)

    assert response.status_code == 409
    assert b"Username is already taken" in response.data
    assert session.query(User).count() == 1


# /login


def test_login_page_renders_form(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'action="/login"' in response.data


def test_login_sets_cookie_and_redirects_home(app, client, session):
    user = create_user(session, username="alice", password="secret")

    response = login(client)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    cookie = get_access_cookie(app, client)
    assert cookie is not None
    with app.app_context():
        assert decode_token(cookie.value)["sub"] == str(user.id)


def test_login_with_wrong_password_shows_error(app, client, session):
    create_user(session, username="alice", password="secret")

    response = login(client, password="wrong")

    assert response.status_code == 401
    assert b"Invalid username or password" in response.data
    assert b'value="alice"' in response.data
    assert get_access_cookie(app, client) is None


def test_login_with_unknown_user_shows_error(app, client):
    response = login(client, username="nobody")

    assert response.status_code == 401
    assert b"Invalid username or password" in response.data
    assert get_access_cookie(app, client) is None


# /logout


def test_logout_removes_cookie_and_redirects_to_login(app, client, session):
    create_user(session, username="alice", password="secret")
    login(client)

    response = client.post("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"
    assert get_access_cookie(app, client) is None
