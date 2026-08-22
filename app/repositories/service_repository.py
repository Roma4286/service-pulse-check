from app.extentions import db
from app.models import Service, ServiceType, ServiceStatus

class ServiceRepository:
    def get_service_by_id(self, service_id: int) -> Service | None:
        return db.session.get(Service, service_id)

    def get_all_active_services(self) -> list[Service]:
        return db.session.query(Service).filter_by(status=ServiceStatus.ACTIVE).all()

    def create_new_service(self, name: str, url: str, type: ServiceType) -> None:
        service = Service(name=name, url=url, type=type, status=ServiceStatus.ACTIVE)
        db.session.add(service)
        db.session.commit()
