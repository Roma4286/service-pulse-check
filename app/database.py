from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker

from .config import settings

engine = create_engine(settings.pg_url, echo=False, pool_pre_ping=True)

Session = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))


def check_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as e:
        raise RuntimeError(
            f"Database is unavailable at {engine.url.host}:{engine.url.port}. Is PostgreSQL running?"
        ) from e
