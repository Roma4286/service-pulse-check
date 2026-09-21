from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from .services.routers import services_bp
api_bp.register_blueprint(services_bp)

from .auth.routers import auth_bp
api_bp.register_blueprint(auth_bp)

from . import error_handlers  # noqa: E402,F401 — registers error handlers on api_bp