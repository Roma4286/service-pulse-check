from sqlalchemy.orm import Session

from app.models import User
from test.api.api_factories import make_user


def create_user(session: Session, *, username: str | None = None, password: str = "password") -> User:
    user = make_user(session, username=username, password=password)
    session.commit()
    return user
