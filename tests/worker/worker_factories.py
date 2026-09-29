from unittest.mock import create_autospec

from app.celery import tasks
from app.celery.checkers.base import BaseChecker
from app.models import ServiceType


def make_checker(
    monkeypatch, service_type: ServiceType, result: tuple[bool, float]
) -> BaseChecker:
    """Put a fake checker that returns `result` in place of the real one for `service_type`."""
    checker = create_autospec(BaseChecker, instance=True)
    checker.check.return_value = result
    monkeypatch.setitem(tasks.CHECKERS, service_type, checker)
    return checker
