from celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from .models import Base

db = SQLAlchemy(model_class=Base)
migrate = Migrate()
celery = Celery(__name__)