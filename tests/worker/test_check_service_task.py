import logging

import pytest

from app.celery import tasks
from app.celery.tasks import check_service_task
from app.models import CheckResult, ResultStatus, ServiceType
from tests.factories import make_service, make_user
from tests.worker.worker_factories import make_checker

pytestmark = pytest.mark.usefixtures("task_session")


def test_task_saves_success_result(monkeypatch, session):
    make_checker(monkeypatch, ServiceType.HTTP, (True, 0.25))
    service = make_service(session, make_user(session))

    check_service_task(service.id, "https://example.com", "http", 5.0)

    result = session.query(CheckResult).one()
    assert result.service_id == service.id
    assert result.status == ResultStatus.SUCCESS
    assert result.response_time == 0.25


def test_task_saves_fail_result(monkeypatch, session):
    make_checker(monkeypatch, ServiceType.HTTP, (False, 5.0))
    service = make_service(session, make_user(session))

    check_service_task(service.id, "https://example.com", "http", 5.0)

    result = session.query(CheckResult).one()
    assert result.status == ResultStatus.FAIL
    assert result.response_time == 5.0


def test_task_uses_http_checker_for_http_service(monkeypatch, session):
    http_checker = make_checker(monkeypatch, ServiceType.HTTP, (True, 0.1))
    tcp_checker = make_checker(monkeypatch, ServiceType.TCP, (True, 0.1))
    service = make_service(session, make_user(session), type=ServiceType.HTTP)

    check_service_task(service.id, "https://example.com", "http", 2.5)

    http_checker.check.assert_called_once_with("https://example.com", 2.5)
    tcp_checker.check.assert_not_called()


def test_task_uses_tcp_checker_for_tcp_service(monkeypatch, session):
    http_checker = make_checker(monkeypatch, ServiceType.HTTP, (True, 0.1))
    tcp_checker = make_checker(monkeypatch, ServiceType.TCP, (True, 0.1))
    service = make_service(session, make_user(session), type=ServiceType.TCP)

    check_service_task(service.id, "db.example.com:5432", "tcp", 2.5)

    tcp_checker.check.assert_called_once_with("db.example.com:5432", 2.5)
    http_checker.check.assert_not_called()


def test_task_logs_and_swallows_save_error(monkeypatch, session, caplog):
    make_checker(monkeypatch, ServiceType.HTTP, (True, 0.25))

    with caplog.at_level(logging.ERROR, logger=tasks.__name__):
        check_service_task(999, "https://example.com", "http", 5.0)

    assert "Failed to save check result for service_id=999" in caplog.text
    assert session.query(CheckResult).count() == 0
