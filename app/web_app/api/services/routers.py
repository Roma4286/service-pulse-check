from flask import Blueprint

from app.repositories.service_repository import ServiceRepository
from app.database import Session as database_session

services_bp = Blueprint('services', __name__, url_prefix='/services')

@services_bp.route('/get_active_services', methods=['GET'])
def get_active_services():
    service_repo = ServiceRepository(database_session())
    services = service_repo.get_active_services()
    return {
        "services": [
            {
                "id": service.id,
                "name": service.name,
                "url": service.url,
                "type": service.type.value,
                "status": service.status.value
            }
            for service in services
        ]
    }