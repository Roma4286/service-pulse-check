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
        "broker_url": REDIS_URL,
        "result_backend": REDIS_URL,
    }

    db.init_app(app)
    migrate.init_app(app, db)

    celery.config_from_object(app.config["CELERY"])
    celery.set_default()
    app.extensions["celery"] = celery

    return app
