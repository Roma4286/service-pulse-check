from datetime import UTC, datetime, timedelta

import pytest

from app.celery import tasks
from app.celery.tasks import purge_old_check_results_task
from app.models import CheckResult
from tests.factories import make_check_result, make_service, make_user

pytestmark = pytest.mark.usefixtures("task_session")


def test_task_deletes_results_older_than_retention(monkeypatch, session):
    monkeypatch.setattr(tasks, "CHECK_RESULTS_RETENTION_DAYS", 7)
    service = make_service(session, make_user(session))
    now = datetime.now(UTC).replace(tzinfo=None)
    make_check_result(session, service, created_at=now - timedelta(days=8))
    recent_result = make_check_result(
        session, service, created_at=now - timedelta(days=6)
    )
    session.commit()

    purge_old_check_results_task()

    assert [result.id for result in session.query(CheckResult)] == [recent_result.id]
