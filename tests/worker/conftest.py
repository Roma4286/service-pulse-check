from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.orm import scoped_session

from app.celery import tasks
from app.celery.checkers import http as http_module
from app.celery.checkers import tcp as tcp_module


@pytest.fixture
def fake_get(monkeypatch):
    get = Mock(return_value=Mock(status_code=200))
    monkeypatch.setattr(http_module.requests, "get", get)
    return get


@pytest.fixture
def fake_create_connection(monkeypatch):
    create_connection = Mock(return_value=MagicMock())
    monkeypatch.setattr(tcp_module, "socket", Mock(create_connection=create_connection))
    return create_connection


@pytest.fixture
def fake_clock(monkeypatch):
    for module in (http_module, tcp_module):
        monkeypatch.setattr(
            module, "time", Mock(monotonic=Mock(side_effect=[100.0, 100.25]))
        )


@pytest.fixture
def task_session(monkeypatch, session):
    monkeypatch.setattr(tasks, "Session", scoped_session(lambda: session))


@pytest.fixture
def celery_app():
    return Mock(name="celery_app")


@pytest.fixture
def entry_class(monkeypatch):
    entry_class = Mock(name="RedBeatSchedulerEntry")
    entry_class.generate_key.return_value = "custom-prefix:check_service_7"
    monkeypatch.setattr(tasks, "RedBeatSchedulerEntry", entry_class)
    return entry_class


@pytest.fixture
def redis(monkeypatch):
    redis = Mock(name="redis")
    monkeypatch.setattr(tasks, "get_redis", Mock(return_value=redis))
    monkeypatch.setattr(tasks, "ensure_conf", Mock())
    return redis
