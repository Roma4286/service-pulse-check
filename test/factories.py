import itertools

from sqlalchemy.orm import Session

from app.models import CheckResult, ResultStatus, Service, ServiceType, User

_usernames = itertools.count(1)


def make_user(session: Session, *, username: str | None = None, password: str = "password") -> User:
    user = User(username=username or f"user{next(_usernames)}", password=password)
    session.add(user)
    session.flush()
    return user


def make_service(
    session: Session,
    user: User,
    *,
    name: str = "demo",
    url: str = "https://example.com",
    type: ServiceType = ServiceType.HTTP,
    is_active: bool = True,
    interval_in_seconds: int = 60,
    timeout_in_seconds: float = 5.0,
) -> Service:
    service = Service(
        name=name,
        url=url,
        type=type,
        is_active=is_active,
        user_id=user.id,
        interval_in_seconds=interval_in_seconds,
        timeout_in_seconds=timeout_in_seconds,
    )
    session.add(service)
    session.flush()
    return service


def make_check_result(
    session: Session,
    service: Service,
    *,
    status: ResultStatus = ResultStatus.SUCCESS,
    response_time: float = 0.1,
) -> CheckResult:
    check_result = CheckResult(
        service_id=service.id,
        status=status,
        response_time=response_time,
    )
    session.add(check_result)
    session.flush()
    return check_result
