from app.models import Service, ServiceType, ServiceStatus
from .base_repository import BaseRepository

class ServiceRepository(BaseRepository):
    def get_service_by_id(self, service_id: int) -> Service | None:
        return self.db_session.get(Service, service_id)

    def get_services(self, is_active: None | bool = None) -> list[Service]:
        if is_active is None:
            return self.db_session.query(Service).all()
        return self.db_session.query(Service)\
            .filter_by(status=ServiceStatus.ACTIVE if is_active else ServiceStatus.INACTIVE).all()

    def create_new_service(self, name: str, url: str, type: ServiceType) -> None:
        service = Service(name=name, url=url, type=type, status=ServiceStatus.ACTIVE)
        self.db_session.add(service)
        self.db_session.commit()
