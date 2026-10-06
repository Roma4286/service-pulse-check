import os
from unittest.mock import create_autospec

import pytest
from flask_jwt_extended import create_access_token, get_csrf_token
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.pool import StaticPool

from app import web_app
from app.celery.tasks import ServiceScheduler
from app.models import Base
from tests.factories import create_user

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture(scope="session")
def engine():
    if TEST_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(engine, "connect")
        def _sqlite_connect(dbapi_connection, connection_record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")
    else:
        engine = create_engine(TEST_DATABASE_URL)

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    session = Session(engine, expire_on_commit=False)
    yield session
    session.close()
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def scheduler():
    return create_autospec(ServiceScheduler)


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
        app.config["JWT_ACCESS_COOKIE_NAME"],
        token,
        path=app.config["JWT_ACCESS_COOKIE_PATH"],
    )
    client.environ_base[csrf_header_key] = csrf_token
    return user
