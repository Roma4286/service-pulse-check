from datetime import timedelta

from flask import Flask, g
from flask_cors import CORS

from app.celery.celery_app import celery_app
from app.celery.tasks import ServiceScheduler
from app.config import settings
from app.database import Session
from app.operations.create_service import CreateService
from app.operations.delete_service import DeleteService
from app.operations.register_user import RegisterUser
from app.operations.update_service import UpdateService
from app.repositories.check_result_repository import CheckResultRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.web_app.api.error_handlers import reformat_spec_validation_error
from app.web_app.extensions import jwt, spec

spec.before = reformat_spec_validation_error


def create_app():
    app = Flask(__name__)
    app.config["FLASK_PYDANTIC_VALIDATION_ERROR_RAISE"] = True
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        hours=settings.jwt_access_token_expires_in_hours
    )
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
    app.config["JWT_COOKIE_SECURE"] = True
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True

    spec.register(app)
    jwt.init_app(app)

    cors_origins = settings.cors_origin_list()
    if cors_origins:
        CORS(
            app,
            resources={r"/api/*": {"origins": cors_origins}},
            supports_credentials=True,
            allow_headers=["Content-Type", app.config["JWT_ACCESS_CSRF_HEADER_NAME"]],
            methods=["GET", "POST", "PATCH", "DELETE"],
        )

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
        g.register_user = RegisterUser(user_repository=g.user_repo)

    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()

    from .api import api_bp

    app.register_blueprint(api_bp)

    from .web import web_bp

    app.register_blueprint(web_bp)

    return app
