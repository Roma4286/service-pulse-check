from unittest.mock import create_autospec

import pytest

from app.celery.tasks import ServiceScheduler


@pytest.fixture
def scheduler():
    return create_autospec(ServiceScheduler)
