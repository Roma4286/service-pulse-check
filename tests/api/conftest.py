import pytest
from flask_jwt_extended import create_access_token
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
def logged_in(app, client, session):
    user = create_user(session)

    with app.app_context():
        token = create_access_token(identity=str(user.id))
    client.set_cookie(
        app.config["JWT_ACCESS_COOKIE_NAME"], token, path=app.config["JWT_ACCESS_COOKIE_PATH"]
    )
    return user
