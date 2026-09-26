import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

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
