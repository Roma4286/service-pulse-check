from flask import Blueprint
from .services.routers import services_bp

api_bp = Blueprint('api', __name__, url_prefix='/api')
api_bp.register_blueprint(services_bp)
