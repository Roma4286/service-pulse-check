import os
from dotenv import load_dotenv

import celery

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL")


config_dict = {
        "broker_url": f"{REDIS_URL}/0",
        "result_backend": f"{REDIS_URL}/1",
        "timezone": "Europe/Moscow",
        "task_track_started": True,

        "beat_scheduler": "redbeat.RedBeatScheduler",
        "redbeat_lock_timeout": 60,
    }

celery_app = celery.Celery("service_pulse_check")

celery_app.conf.update(config_dict)
celery_app.set_default()