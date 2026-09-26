import pytest
from sqlalchemy.exc import IntegrityError

from app.models import CheckResult, ResultStatus
from app.repositories.check_result_repository import CheckResultRepository
from factories import make_check_result, make_service, make_user


def test_create_result_persists_result(session):
    repository = CheckResultRepository(session)
    service = make_service(session, make_user(session))

    result = repository.create_result(service.id, ResultStatus.FAIL, 1.5)

    assert result.id is not None
    assert result.service_id == service.id
    assert result.status == ResultStatus.FAIL
    assert result.response_time == 1.5
    assert session.query(CheckResult).filter_by(id=result.id).count() == 1


def test_create_result_in_transaction_is_not_committed(session):
    repository = CheckResultRepository(session)
    service = make_service(session, make_user(session))
    session.commit()

    repository.create_result(service.id, ResultStatus.SUCCESS, 0.1, is_db_transaction=True)
    repository.db_rollback()

    assert session.query(CheckResult).count() == 0


def test_create_result_with_missing_service_raises(session):
    repository = CheckResultRepository(session)

    with pytest.raises(IntegrityError):
        repository.create_result(999, ResultStatus.SUCCESS, 0.1)
    session.rollback()

    assert session.query(CheckResult).count() == 0


def test_get_result_by_service_id_returns_only_service_results(session):
    repository = CheckResultRepository(session)
    user = make_user(session)
    service = make_service(session, user)
    other_service = make_service(session, user)
    first_result = make_check_result(session, service, status=ResultStatus.SUCCESS)
    second_result = make_check_result(session, service, status=ResultStatus.FAIL)
    make_check_result(session, other_service)
    session.expunge_all()

    results = repository.get_result_by_service_id(service.id)

    assert {result.id for result in results} == {first_result.id, second_result.id}


def test_get_result_by_service_id_returns_empty_list_when_none(session):
    service = make_service(session, make_user(session))

    assert CheckResultRepository(session).get_result_by_service_id(service.id) == []


def test_delete_result(session):
    repository = CheckResultRepository(session)
    service = make_service(session, make_user(session))
    result = make_check_result(session, service)
    other_result = make_check_result(session, service)

    assert repository.delete_result(result.id, service.id) is True
    assert [row.id for row in session.query(CheckResult).all()] == [other_result.id]


def test_delete_result_in_transaction_is_not_committed(session):
    repository = CheckResultRepository(session)
    service = make_service(session, make_user(session))
    result = make_check_result(session, service)
    session.commit()

    repository.delete_result(result.id, service.id, is_db_transaction=True)
    repository.db_rollback()

    assert session.query(CheckResult).count() == 1


def test_delete_result_returns_false_when_missing(session):
    service = make_service(session, make_user(session))

    assert CheckResultRepository(session).delete_result(999, service.id) is False


def test_delete_result_returns_false_for_other_service(session):
    repository = CheckResultRepository(session)
    user = make_user(session)
    service = make_service(session, user)
    other_service = make_service(session, user)
    result = make_check_result(session, service)

    assert repository.delete_result(result.id, other_service.id) is False
    assert session.query(CheckResult).count() == 1


def test_delete_results_by_service_id(session):
    repository = CheckResultRepository(session)
    user = make_user(session)
    service = make_service(session, user)
    other_service = make_service(session, user)
    make_check_result(session, service)
    make_check_result(session, service)
    other_result = make_check_result(session, other_service)

    deleted = repository.delete_results_by_service_id(service.id)

    assert deleted == 2
    assert [row.id for row in session.query(CheckResult).all()] == [other_result.id]


def test_delete_results_by_service_id_returns_zero_when_none(session):
    service = make_service(session, make_user(session))

    assert CheckResultRepository(session).delete_results_by_service_id(service.id) == 0


def test_delete_results_by_service_id_in_transaction_is_not_committed(session):
    repository = CheckResultRepository(session)
    service = make_service(session, make_user(session))
    make_check_result(session, service)
    make_check_result(session, service)
    session.commit()

    repository.delete_results_by_service_id(service.id, is_db_transaction=True)
    repository.db_rollback()

    assert session.query(CheckResult).count() == 2
