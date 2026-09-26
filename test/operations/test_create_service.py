import pytest

from app.models import Service, ServiceType
from app.operations.create_service import CreateService, CreateServiceDTO
from app.operations.errors import ServicePersistenceError, ServiceSchedulingError
from app.repositories.service_repository import ServiceRepository
from factories import make_user


def make_dto(user_id: int, *, is_active: bool = True) -> CreateServiceDTO:
    return CreateServiceDTO(
        name="api",
        url="https://api.example.com",
        type=ServiceType.HTTP,
        is_active=is_active,
        user_id=user_id,
        interval_in_seconds=30,
        timeout_in_seconds=2.5,
    )


@pytest.fixture
def create_service(session, scheduler):
    return CreateService(scheduler=scheduler, service_repository=ServiceRepository(session))


def test_create_active_service_persists_and_schedules(session, scheduler, create_service):
    user = make_user(session)

    service = create_service(dto=make_dto(user.id))

    assert service.id is not None
    assert service.name == "api"

    session.rollback()
    assert session.query(Service).filter_by(id=service.id).count() == 1
    scheduler.create_task.assert_called_once_with(
        service_id=service.id,
        url="https://api.example.com",
        service_type=ServiceType.HTTP,
        interval_in_seconds=30,
        timeout_in_seconds=2.5,
    )


def test_create_inactive_service_persists_without_scheduling(session, scheduler, create_service):
    user = make_user(session)

    service = create_service(dto=make_dto(user.id, is_active=False))
    session.rollback()

    assert session.query(Service).filter_by(id=service.id).count() == 1
    scheduler.create_task.assert_not_called()


def test_create_service_rolls_back_when_scheduling_fails(session, scheduler, create_service):
    user = make_user(session)
    session.commit()
    scheduler.create_task.side_effect = RuntimeError("redis is down")

    with pytest.raises(ServiceSchedulingError) as exc_info:
        create_service(dto=make_dto(user.id))

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert "service_id" in exc_info.value.context
    assert session.query(Service).count() == 0


def test_create_service_with_missing_user_raises(session, scheduler, create_service):
    with pytest.raises(ServicePersistenceError) as exc_info:
        create_service(dto=make_dto(user_id=999))
    session.rollback()

    assert exc_info.value.context == {"name": "api", "url": "https://api.example.com"}
    assert session.query(Service).count() == 0
    scheduler.create_task.assert_not_called()
