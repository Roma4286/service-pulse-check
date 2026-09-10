from app.models import Service, ServiceType
from .base_repository import BaseRepository

class ServiceRepository(BaseRepository):
    def get_service_by_id(self, user_id: int, service_id: int) -> Service | None:
        service = self.db_session.query(Service).filter_by(id=service_id, user_id=user_id).first()
        
        if service is not None:
            self.db_session.expunge(service)
        return service

    def get_services(self, user_id: int, is_active: bool | None = None) -> list[Service]:
        query = self.db_session.query(Service)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        query = query.filter_by(user_id=user_id)
        services = query.all()
        for service in services:
            self.db_session.expunge(service)
        return services

    def create_new_service(self, name: str, url: str, type: ServiceType, is_active: bool, user_id: int, interval_in_seconds: int, timeout_in_seconds: float, is_db_transaction: bool = False) -> Service:
        service = Service(
            name=name, url=url, type=type, is_active=is_active, user_id=user_id,
            interval_in_seconds=interval_in_seconds, timeout_in_seconds=timeout_in_seconds,
        )
        self.db_session.add(service)

        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        self.db_session.expunge(service)
        return service

    def update_service(self,
                        service_id: int,
                        user_id: int,
                        name: str | None = None,
                        url: str | None = None,
                        type: ServiceType | None = None,
                        is_active: bool | None = None,
                        interval_in_seconds: int | None = None,
                        timeout_in_seconds: float | None = None,
                        is_db_transaction: bool = False) -> Service | None:
        service = self.db_session.query(Service).filter_by(id=service_id, user_id=user_id).first()
        if service is None:
            return None

        if name is not None:
            service.name = name
        if url is not None:
            service.url = url
        if type is not None:
            service.type = type
        if is_active is not None:
            service.is_active = is_active
        if interval_in_seconds is not None:
            service.interval_in_seconds = interval_in_seconds
        if timeout_in_seconds is not None:
            service.timeout_in_seconds = timeout_in_seconds

        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        self.db_session.expunge(service)
        return service

    def delete_service(self, user_id: int, service_id: int, is_db_transaction: bool = False) -> bool:
        service = self.db_session.query(Service).filter_by(id=service_id, user_id=user_id).first()
        if service is None:
            return False

        self.db_session.delete(service)

        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        return True
