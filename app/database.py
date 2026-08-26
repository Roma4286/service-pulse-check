from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .config import settings

engine = create_engine(settings.pg_url, echo=False)

Session = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))
