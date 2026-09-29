import pytest

from app.celery.tasks import ServiceScheduler, check_service_task
from app.models import ServiceType


def test_create_task_saves_redbeat_entry(celery_app, entry_class):
    ServiceScheduler(celery_app).create_task(
        service_id=7,
        url="https://example.com",
        service_type=ServiceType.HTTP,
        interval_in_seconds=60,
        timeout_in_seconds=5.0,
    )

    entry_class.assert_called_once_with(
        name="check_service_7",
        task="check_service",
        schedule=60,
        args=[7, "https://example.com", "http", 5.0],
        options={"expires": 59},
        app=celery_app,
    )
    entry_class.return_value.save.assert_called_once_with()


def test_create_task_schedules_registered_task(celery_app, entry_class):
    ServiceScheduler(celery_app).create_task(
        service_id=7,
        url="https://example.com",
        service_type=ServiceType.HTTP,
        interval_in_seconds=60,
        timeout_in_seconds=5.0,
    )

    assert entry_class.call_args.kwargs["task"] == check_service_task.name


@pytest.mark.parametrize(("exists", "expected"), [(1, True), (0, False)])
def test_task_exists_checks_redis_key(celery_app, entry_class, redis, exists, expected):
    redis.exists.return_value = exists

    assert ServiceScheduler(celery_app).task_exists(7) is expected
    entry_class.generate_key.assert_called_once_with(celery_app, "check_service_7")
    redis.exists.assert_called_once_with("custom-prefix:check_service_7")


def test_delete_task_deletes_existing_entry(celery_app, entry_class, redis):
    redis.exists.return_value = 1

    ServiceScheduler(celery_app).delete_task(7)

    entry_class.from_key.assert_called_once_with(
        "custom-prefix:check_service_7", app=celery_app
    )
    entry_class.from_key.return_value.delete.assert_called_once_with()


def test_delete_task_skips_missing_entry(celery_app, entry_class, redis):
    redis.exists.return_value = 0

    ServiceScheduler(celery_app).delete_task(7)

    entry_class.from_key.assert_not_called()
