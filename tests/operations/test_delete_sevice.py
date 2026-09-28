import pytest
from factories import make_service, make_user

from app.models import Service
from app.operations.delete_service import DeleteService, DeleteServiceDTO
from app.operations.errors import ServiceNotFoundError, ServiceSchedulingError
from app.repositories.service_repository import ServiceRepository


@pytest.fixture
def delete_service(session, scheduler):
    return DeleteService(
        scheduler=scheduler, service_repository=ServiceRepository(session)
    )


def test_delete_service_removes_service_and_task(session, scheduler, delete_service):
    user = make_user(session)
    service = make_service(session, user)

    result = delete_service(
        dto=DeleteServiceDTO(user_id=user.id, service_id=service.id)
    )
    session.rollback()

    assert result is True
    assert session.query(Service).count() == 0
    scheduler.delete_task.assert_called_once_with(service.id)


def test_delete_service_raises_when_missing(session, scheduler, delete_service):
    user = make_user(session)

    with pytest.raises(ServiceNotFoundError):
        delete_service(dto=DeleteServiceDTO(user_id=user.id, service_id=999))

    scheduler.delete_task.assert_not_called()


def test_delete_service_raises_for_other_user(session, scheduler, delete_service):
    service = make_service(session, make_user(session))
    other_user = make_user(session)

    with pytest.raises(ServiceNotFoundError):
        delete_service(
            dto=DeleteServiceDTO(user_id=other_user.id, service_id=service.id)
        )

    assert session.query(Service).count() == 1
    scheduler.delete_task.assert_not_called()


def test_delete_service_rolls_back_when_scheduling_fails(
    session, scheduler, delete_service
):
    user = make_user(session)
    service = make_service(session, user)
    session.commit()
    scheduler.delete_task.side_effect = RuntimeError("redis is down")

    with pytest.raises(ServiceSchedulingError) as exc_info:
        delete_service(dto=DeleteServiceDTO(user_id=user.id, service_id=service.id))

    assert exc_info.value.context == {"service_id": service.id}
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert session.query(Service).count() == 1
