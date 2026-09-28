from sqlalchemy.orm import Session

from app.models import CheckResult, Service, User
from tests.factories import make_check_result, make_service, make_user


def create_user(session: Session, *, username: str | None = None, password: str = "password") -> User:
    user = make_user(session, username=username, password=password)
    session.commit()
    return user


def create_service(session: Session, user: User, **fields) -> Service:
    service = make_service(session, user, **fields)
    session.commit()
    return service


def create_check_result(session: Session, service: Service, **fields) -> CheckResult:
    check_result = make_check_result(session, service, **fields)
    session.commit()
    return check_result
