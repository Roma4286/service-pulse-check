import pytest
from sqlalchemy.exc import IntegrityError

from app.models import CheckResult, Service, ServiceType
from app.repositories.service_repository import ServiceRepository
from factories import make_check_result, make_service, make_user


def test_create_new_service_persists_service(session):
    repository = ServiceRepository(session)
    user = make_user(session)

    service = repository.create_new_service(
        name="api",
        url="https://api.example.com",
        type=ServiceType.HTTP,
        is_active=True,
        user_id=user.id,
        interval_in_seconds=30,
        timeout_in_seconds=2.5,
    )

    assert service.id is not None
    assert service.name == "api"
    assert service.url == "https://api.example.com"
    assert service.type == ServiceType.HTTP
    assert service.is_active is True
    assert service.user_id == user.id
    assert service.interval_in_seconds == 30
    assert service.timeout_in_seconds == 2.5
    assert session.query(Service).filter_by(id=service.id).count() == 1


def test_create_new_service_in_transaction_is_not_committed(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    session.commit()

    repository.create_new_service(
        name="api",
        url="https://api.example.com",
        type=ServiceType.HTTP,
        is_active=True,
        user_id=user.id,
        interval_in_seconds=30,
        timeout_in_seconds=2.5,
        is_db_transaction=True,
    )
    repository.db_rollback()

    assert session.query(Service).count() == 0


def test_create_new_service_with_missing_user_raises(session):
    repository = ServiceRepository(session)

    with pytest.raises(IntegrityError):
        repository.create_new_service(
            name="api",
            url="https://api.example.com",
            type=ServiceType.HTTP,
            is_active=True,
            user_id=999,
            interval_in_seconds=30,
            timeout_in_seconds=2.5,
        )
    session.rollback()

    assert session.query(Service).count() == 0


def test_get_service_by_id(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    new_service = make_service(session, user)
    session.expunge_all()

    service = repository.get_service_by_id(user.id, new_service.id)

    assert service is not None
    assert service.id == new_service.id
    assert service.name == new_service.name
    assert service.user_id == user.id


def test_get_service_by_id_returns_none_when_missing(session):
    user = make_user(session)

    assert ServiceRepository(session).get_service_by_id(user.id, 999) is None


def test_get_service_by_id_returns_none_for_other_user(session):
    owner = make_user(session)
    other_user = make_user(session)
    service = make_service(session, owner)

    assert ServiceRepository(session).get_service_by_id(other_user.id, service.id) is None


def test_get_services_returns_only_user_services(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    other_user = make_user(session)
    first_service = make_service(session, user, name="first")
    second_service = make_service(session, user, name="second")
    make_service(session, other_user, name="foreign")
    session.expunge_all()

    services = repository.get_services(user.id)

    assert {service.id for service in services} == {first_service.id, second_service.id}


@pytest.mark.parametrize("is_active", [True, False])
def test_get_services_filters_by_is_active(session, is_active):
    repository = ServiceRepository(session)
    user = make_user(session)
    active_service = make_service(session, user, is_active=True)
    inactive_service = make_service(session, user, is_active=False)
    expected_service = active_service if is_active else inactive_service
    session.expunge_all()

    services = repository.get_services(user.id, is_active=is_active)

    assert [service.id for service in services] == [expected_service.id]


def test_get_services_returns_empty_list_when_user_has_none(session):
    user = make_user(session)

    assert ServiceRepository(session).get_services(user.id) == []


def test_update_service_changes_only_given_fields(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    new_service = make_service(session, user, name="old", url="https://old.example.com")

    service = repository.update_service(new_service.id, user.id, name="new", is_active=False)
    session.expunge_all()
    stored_service = session.get(Service, new_service.id)

    assert service is not None
    assert service.name == "new"
    assert stored_service.name == "new"
    assert stored_service.is_active is False
    assert stored_service.url == "https://old.example.com"
    assert stored_service.type == ServiceType.HTTP


def test_update_service_changes_all_fields(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    new_service = make_service(session, user)

    repository.update_service(
        new_service.id,
        user.id,
        name="db",
        url="db.example.com:5432",
        type=ServiceType.TCP,
        is_active=False,
        interval_in_seconds=120,
        timeout_in_seconds=10.0,
    )
    session.expunge_all()
    stored_service = session.get(Service, new_service.id)

    assert stored_service.name == "db"
    assert stored_service.url == "db.example.com:5432"
    assert stored_service.type == ServiceType.TCP
    assert stored_service.is_active is False
    assert stored_service.interval_in_seconds == 120
    assert stored_service.timeout_in_seconds == 10.0


def test_update_service_in_transaction_is_not_committed(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    new_service = make_service(session, user, name="old")
    session.commit()

    repository.update_service(new_service.id, user.id, name="new", is_db_transaction=True)
    repository.db_rollback()
    session.expunge_all()

    assert session.get(Service, new_service.id).name == "old"


def test_update_service_returns_none_when_missing(session):
    user = make_user(session)

    assert ServiceRepository(session).update_service(999, user.id, name="new") is None


def test_update_service_returns_none_for_other_user(session):
    repository = ServiceRepository(session)
    owner = make_user(session)
    other_user = make_user(session)
    new_service = make_service(session, owner, name="old")

    service = repository.update_service(new_service.id, other_user.id, name="new")
    session.expunge_all()

    assert service is None
    assert session.get(Service, new_service.id).name == "old"


def test_delete_service(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    service = make_service(session, user)

    assert repository.delete_service(user.id, service.id) is True
    assert session.query(Service).count() == 0


def test_delete_service_deletes_its_check_results(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    service = make_service(session, user)
    make_check_result(session, service)
    make_check_result(session, service)

    repository.delete_service(user.id, service.id)

    assert session.query(CheckResult).count() == 0


def test_delete_service_in_transaction_is_not_committed(session):
    repository = ServiceRepository(session)
    user = make_user(session)
    service = make_service(session, user)
    session.commit()

    repository.delete_service(user.id, service.id, is_db_transaction=True)
    repository.db_rollback()

    assert session.query(Service).count() == 1


def test_delete_service_returns_false_when_missing(session):
    user = make_user(session)

    assert ServiceRepository(session).delete_service(user.id, 999) is False


def test_delete_service_returns_false_for_other_user(session):
    repository = ServiceRepository(session)
    owner = make_user(session)
    other_user = make_user(session)
    service = make_service(session, owner)

    assert repository.delete_service(other_user.id, service.id) is False
    assert session.query(Service).count() == 1
