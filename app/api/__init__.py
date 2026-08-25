from flask import Flask

from app.database import Session


def create_app():
    app = Flask(__name__)

    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()

    return app
