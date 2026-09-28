import pytest
from flask_jwt_extended import create_access_token, get_csrf_token
from sqlalchemy.orm import scoped_session

import app.web_app as web_app
from tests.api.api_factories import create_user


@pytest.fixture
def app(monkeypatch, session, scheduler):
    monkeypatch.setattr(web_app, "Session", scoped_session(lambda: session))
    flask_app = web_app.create_app()
    flask_app.config["TESTING"] = True
    flask_app.extensions["scheduler"] = scheduler
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf_header_key(app):
    return "HTTP_" + app.config["JWT_ACCESS_CSRF_HEADER_NAME"].upper().replace("-", "_")


@pytest.fixture
def logged_in(app, client, session, csrf_header_key):
    user = create_user(session)

    with app.app_context():
        token = create_access_token(identity=str(user.id))
        csrf_token = get_csrf_token(token)
    client.set_cookie(
        app.config["JWT_ACCESS_COOKIE_NAME"], token, path=app.config["JWT_ACCESS_COOKIE_PATH"]
    )
    client.environ_base[csrf_header_key] = csrf_token
    return user
