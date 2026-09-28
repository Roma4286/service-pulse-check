import os
from unittest.mock import create_autospec

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.pool import StaticPool

import app.web_app as web_app
from app.celery.tasks import ServiceScheduler
from app.models import Base

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
