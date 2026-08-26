from flask import Blueprint, abort, request

from app.repositories.service_repository import ServiceRepository
from app.database import Session as database_session

services_bp = Blueprint('services', __name__, url_prefix='/services')

STATUS_TO_IS_ACTIVE = {
    "active": True,
    "inactive": False,
}

@services_bp.route('', methods=['GET'])
def get_services():
    status = request.args.get('status')
    if status is None:
        is_active = None
    elif status in STATUS_TO_IS_ACTIVE:
        is_active = STATUS_TO_IS_ACTIVE[status]
    else:
        abort(400, description="status must be 'active' or 'inactive'")

    service_repo = ServiceRepository(database_session())
    services = service_repo.get_services(is_active=is_active)
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