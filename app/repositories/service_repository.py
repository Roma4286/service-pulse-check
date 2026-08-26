from app.models import Service, ServiceType, ServiceStatus
from .base_repository import BaseRepository

class ServiceRepository(BaseRepository):
    def get_service_by_id(self, service_id: int) -> Service | None:
        service = self.db_session.get(Service, service_id)
        if service is not None:
            self.db_session.expunge(service)
        return service

    def get_services(self, is_active: bool | None = None) -> list[Service]:
        query = self.db_session.query(Service)
        if is_active is not None:
            query = query.filter_by(status=ServiceStatus.ACTIVE if is_active else ServiceStatus.INACTIVE)

        services = query.all()
        for service in services:
            self.db_session.expunge(service)
        return services

    def create_new_service(self, name: str, url: str, type: ServiceType, is_db_transaction: bool = False) -> Service:
        service = Service(name=name, url=url, type=type, status=ServiceStatus.ACTIVE)
        self.db_session.add(service)

        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        self.db_session.expunge(service)
        return service

    def update_service(self,
                        service_id: int,
                        name: str | None = None,
                        url: str | None = None,
                        type: ServiceType | None = None,
                        status: ServiceStatus | None = None,
                        is_db_transaction: bool = False) -> Service | None:
        service = self.db_session.get(Service, service_id)
        if service is None:
            return None

        if name is not None:
            service.name = name
        if url is not None:
            service.url = url
        if type is not None:
            service.type = type
        if status is not None:
            service.status = status

        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        self.db_session.expunge(service)
        return service

    def delete_service(self, service_id: int, is_db_transaction: bool = False) -> bool:
        service = self.db_session.get(Service, service_id)
        if service is None:
            return False

        self.db_session.delete(service)

        if not is_db_transaction:
            self.db_session.commit()

        return True
