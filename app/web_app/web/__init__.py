from flask import Blueprint

web_bp = Blueprint(
    "web",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/web/static",
)

from .auth.routes import auth_bp
from .services.routes import services_bp

web_bp.register_blueprint(auth_bp)
web_bp.register_blueprint(services_bp)

from . import (
    error_handlers,  # noqa: F401 — registers error handlers on web_bp
    routes,  # noqa: F401 — registers page routes on web_bp
)
