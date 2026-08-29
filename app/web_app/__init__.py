from flask import Flask, g
from flask_pydantic_spec import FlaskPydanticSpec

from app.database import Session
from app.repositories.service_repository import ServiceRepository
from app.repositories.check_result_repository import CheckResultRepository
from app.celery.celery_app import celery_app
from app.celery.tasks import ServiceScheduler
from app.operations.create_service import CreateService

spec = FlaskPydanticSpec("flask", title="Service Pulse Check API", version="1.0.0")

from app.web_app.api.responses import reformat_spec_validation_error  # noqa: E402

spec.before = reformat_spec_validation_error


def create_app():
    app = Flask(__name__)
    app.config["FLASK_PYDANTIC_VALIDATION_ERROR_RAISE"] = True

    spec.register(app)

    app.extensions["scheduler"] = ServiceScheduler(celery_app)

    @app.before_request
    def inject_repositories():
        session = Session()
        g.service_repo = ServiceRepository(session)
        g.check_result_repo = CheckResultRepository(session)
        g.create_service = CreateService(
            scheduler=app.extensions["scheduler"],
            service_repository=g.service_repo,
        )

    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()

    from .api import api_bp
    app.register_blueprint(api_bp)

    return app
