from flask import Flask
from flask_pydantic_spec import FlaskPydanticSpec

from app.database import Session

spec = FlaskPydanticSpec("flask", title="Service Pulse Check API", version="1.0.0")

from app.web_app.api.responses import reformat_spec_validation_error  # noqa: E402

spec.before = reformat_spec_validation_error


def create_app():
    app = Flask(__name__)
    app.config["FLASK_PYDANTIC_VALIDATION_ERROR_RAISE"] = True

    spec.register(app)

    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()

    from .api import api_bp
    app.register_blueprint(api_bp)

    return app
