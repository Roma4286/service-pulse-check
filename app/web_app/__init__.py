from datetime import timedelta
from flask import Flask, g

from app.config import settings
from app.database import Session
from app.repositories.service_repository import ServiceRepository
from app.repositories.check_result_repository import CheckResultRepository
from app.repositories.user_repository import UserRepository
from app.celery.celery_app import celery_app
from app.celery.tasks import ServiceScheduler
from app.operations.create_service import CreateService
from app.operations.update_service import UpdateService
from app.operations.delete_service import DeleteService
from app.web_app.extensions import jwt, spec
from app.web_app.api.responses import reformat_spec_validation_error

spec.before = reformat_spec_validation_error


def create_app():
    app = Flask(__name__)
    app.config["FLASK_PYDANTIC_VALIDATION_ERROR_RAISE"] = True
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=settings.jwt_access_token_expires_in_hours)

    spec.register(app)
    jwt.init_app(app)

    app.extensions["scheduler"] = ServiceScheduler(celery_app)

    @app.before_request
    def inject_dependencies():
        session = Session()
        g.service_repo = ServiceRepository(session)
        g.check_result_repo = CheckResultRepository(session)
        g.user_repo = UserRepository(session)
        g.create_service = CreateService(
            scheduler=app.extensions["scheduler"],
            service_repository=g.service_repo,
        )
        g.update_service = UpdateService(
            scheduler=app.extensions["scheduler"],
            service_repository=g.service_repo,
        )
        g.delete_service = DeleteService(
            scheduler=app.extensions["scheduler"],
            service_repository=g.service_repo,
        )

    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()

    from .api import api_bp
    app.register_blueprint(api_bp)

    return app
