import os
from dotenv import load_dotenv

from flask import Flask

from .extentions import celery, db, migrate

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL")

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["CELERY"] = {
        "broker_url": f"{REDIS_URL}/0",
        "result_backend": f"{REDIS_URL}/1",
        "timezone": "Europe/Moscow",
        "task_track_started": True,

        "beat_scheduler": "redbeat.RedBeatScheduler",
        "redbeat_lock_timeout": 60,
    }

    db.init_app(app)
    migrate.init_app(app, db)

    class FlaskTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskTask
    celery.config_from_object(app.config["CELERY"])
    celery.set_default()
    app.extensions["celery"] = celery

    return app
