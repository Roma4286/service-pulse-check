import celery

from ..config import settings

config_dict = {
        "broker_url": f"{settings.redis_url}/0",
        "result_backend": f"{settings.redis_url}/1",
        "timezone": "Europe/Moscow",
        "task_track_started": True,

        "beat_scheduler": "redbeat.RedBeatScheduler",
        "redbeat_lock_timeout": 60,

        "beat_max_loop_interval": 30,
    }

celery_app = celery.Celery("service_pulse_check")

celery_app.conf.update(config_dict)
celery_app.set_default()