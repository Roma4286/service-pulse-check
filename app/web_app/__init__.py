from flask import Flask

from app.database import Session


def create_app():
    app = Flask(__name__)
    app.config["FLASK_PYDANTIC_VALIDATION_ERROR_RAISE"] = True

    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()

    from .api import api_bp
    app.register_blueprint(api_bp)

    return app
