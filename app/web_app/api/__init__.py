from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from .services.routers import services_bp

api_bp.register_blueprint(services_bp)
