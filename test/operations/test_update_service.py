from unittest.mock import call, patch

import pytest

from app.models import Service, ServiceType
from app.operations.errors import (
    ServiceNotFoundError,
    ServicePersistenceError,
    ServiceSchedulingError,
    TimeoutGreaterThanIntervalError,
)
from app.operations.update_service import UpdateService, UpdateServiceDTO
from app.repositories.service_repository import ServiceRepository
from factories import make_service, make_user


def make_dto(
    service: Service,
    *,
    user_id: int | None = None,
    name: str | None = None,
    is_active: bool | None = None,
    interval_in_seconds: int | None = None,
    timeout_in_seconds: float | None = None,
) -> UpdateServiceDTO:
    return UpdateServiceDTO(
        service_id=service.id,
        user_id=user_id if user_id is not None else service.user_id,
        name=name,
        is_active=is_active,
        interval_in_seconds=interval_in_seconds,
        timeout_in_seconds=timeout_in_seconds,
    )


@pytest.fixture
def update_service(session, scheduler):
    return UpdateService(scheduler=scheduler, service_repository=ServiceRepository(session))


def get_stored_service(session, service_id: int) -> Service:
    session.expunge_all()
    return session.get(Service, service_id)


def test_update_service_name_without_rescheduling(session, scheduler, update_service):
    service = make_service(session, make_user(session), name="old")

    updated_service = update_service(dto=make_dto(service, name="new"))
    session.rollback()

    assert updated_service.name == "new"
    assert get_stored_service(session, service.id).name == "new"
    assert scheduler.method_calls == []


def test_update_service_deactivation_deletes_task(session, scheduler, update_service):
    service = make_service(session, make_user(session), is_active=True)

    update_service(dto=make_dto(service, is_active=False))

    assert get_stored_service(session, service.id).is_active is False
    scheduler.delete_task.assert_called_once_with(service.id)
    scheduler.create_task.assert_not_called()


def test_update_service_activation_creates_task(session, scheduler, update_service):
    service = make_service(session, make_user(session), is_active=False)

    update_service(dto=make_dto(service, is_active=True))

    assert get_stored_service(session, service.id).is_active is True
    scheduler.delete_task.assert_not_called()
    scheduler.create_task.assert_called_once_with(
        service_id=service.id,
        url=service.url,
        service_type=ServiceType.HTTP,
        interval_in_seconds=service.interval_in_seconds,
        timeout_in_seconds=service.timeout_in_seconds,
    )


@pytest.mark.parametrize(
    ("interval_in_seconds", "timeout_in_seconds"),
    [(120, None), (None, 10.0), (120, 10.0)],
    ids=["interval", "timeout", "both"],
)
def test_update_active_service_schedule_recreates_task(
    session, scheduler, update_service, interval_in_seconds, timeout_in_seconds
):
    service = make_service(session, make_user(session), interval_in_seconds=60, timeout_in_seconds=5.0)
    expected_interval = interval_in_seconds or 60
    expected_timeout = timeout_in_seconds or 5.0

    update_service(
        dto=make_dto(service, interval_in_seconds=interval_in_seconds, timeout_in_seconds=timeout_in_seconds)
    )

    stored_service = get_stored_service(session, service.id)
    assert stored_service.interval_in_seconds == expected_interval
    assert stored_service.timeout_in_seconds == expected_timeout
    assert scheduler.method_calls == [
        call.delete_task(service.id),
        call.create_task(
            service_id=service.id,
            url=service.url,
            service_type=ServiceType.HTTP,
            interval_in_seconds=expected_interval,
            timeout_in_seconds=expected_timeout,
        ),
    ]


def test_update_inactive_service_schedule_does_not_touch_scheduler(session, scheduler, update_service):
    service = make_service(session, make_user(session), is_active=False)

    update_service(dto=make_dto(service, interval_in_seconds=120))

    assert get_stored_service(session, service.id).interval_in_seconds == 120
    assert scheduler.method_calls == []


def test_update_service_with_same_schedule_does_not_reschedule(session, scheduler, update_service):
    service = make_service(session, make_user(session), interval_in_seconds=60, timeout_in_seconds=5.0)

    update_service(dto=make_dto(service, interval_in_seconds=60, timeout_in_seconds=5.0))

    assert scheduler.method_calls == []


def test_update_service_raises_when_missing(session, scheduler, update_service):
    user = make_user(session)
    dto = UpdateServiceDTO(
        service_id=999, user_id=user.id, name="new",
        is_active=None, interval_in_seconds=None, timeout_in_seconds=None,
    )

    with pytest.raises(ServiceNotFoundError):
        update_service(dto=dto)

    assert scheduler.method_calls == []


def test_update_service_raises_for_other_user(session, scheduler, update_service):
    service = make_service(session, make_user(session), name="old")
    other_user = make_user(session)

    with pytest.raises(ServiceNotFoundError):
        update_service(dto=make_dto(service, user_id=other_user.id, name="new"))

    assert get_stored_service(session, service.id).name == "old"
    assert scheduler.method_calls == []


@pytest.mark.parametrize(
    ("interval_in_seconds", "timeout_in_seconds"),
    [(None, 61.0), (4, None), (10, 20.0)],
    ids=["timeout-above-current-interval", "interval-below-current-timeout", "both"],
)
def test_update_service_with_timeout_greater_than_interval_raises(
    session, scheduler, update_service, interval_in_seconds, timeout_in_seconds
):
    service = make_service(session, make_user(session), interval_in_seconds=60, timeout_in_seconds=5.0)

    with pytest.raises(TimeoutGreaterThanIntervalError):
        update_service(
            dto=make_dto(service, interval_in_seconds=interval_in_seconds, timeout_in_seconds=timeout_in_seconds)
        )

    stored_service = get_stored_service(session, service.id)
    assert stored_service.interval_in_seconds == 60
    assert stored_service.timeout_in_seconds == 5.0
    assert scheduler.method_calls == []


def test_update_service_rolls_back_when_scheduling_fails(session, scheduler, update_service):
    service = make_service(session, make_user(session), is_active=True)
    session.commit()
    scheduler.delete_task.side_effect = RuntimeError("redis is down")

    with pytest.raises(ServiceSchedulingError) as exc_info:
        update_service(dto=make_dto(service, is_active=False))

    assert exc_info.value.context == {"service_id": service.id}
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert get_stored_service(session, service.id).is_active is True


def test_update_service_wraps_persistence_error(session, scheduler):
    service_repository = ServiceRepository(session)
    update_service = UpdateService(scheduler=scheduler, service_repository=service_repository)
    service = make_service(session, make_user(session))

    with patch.object(service_repository, "update_service", side_effect=RuntimeError("db is down")):
        with pytest.raises(ServicePersistenceError) as exc_info:
            update_service(dto=make_dto(service, name="new"))

    assert exc_info.value.context == {"service_id": service.id, "name": "new"}
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert scheduler.method_calls == []
