import logging
from celery import Celery
from redbeat import RedBeatSchedulerEntry

from app.celery.checkers.base import BaseChecker
from app.repositories.check_result_repository import CheckResultRepository
from ..database import Session
from .celery_app import celery_app
from .checkers.http import HttpChecker
from .checkers.tcp import TcpChecker
from ..models import ServiceType, ResultStatus

logger = logging.getLogger(__name__)

celery = celery_app

CHECKERS: dict[ServiceType, BaseChecker] = {
    ServiceType.HTTP: HttpChecker(),
    ServiceType.TCP: TcpChecker(),
}

@celery.task(name="check_service")
def check_service_task(service_id: int, url: str, service_type: str):
    checker = CHECKERS[ServiceType(service_type)]
    status, response_time = checker.check(url)
    session = Session()
    try: 
        CheckResultRepository(session).create_result(
            service_id, ResultStatus.SUCCESS if status else ResultStatus.FAIL, response_time
        )
    except Exception as e:
        logger.exception("Failed to save check result for service_id=%s", service_id)
    finally:
        Session.remove()



class ServiceScheduler():
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app

    def create_task(self, service_id: int, url: str, service_type: ServiceType, interval_in_seconds: int):
        entry = RedBeatSchedulerEntry(
            name=f"check_service_{service_id}",
            task="check_service",
            schedule=interval_in_seconds,
            args=[service_id, url, service_type.value],
            options={"expires": interval_in_seconds-1},
            app=self.celery_app,
        )
        entry.save()

    def delete_task(self, service_id: int):
        entry = RedBeatSchedulerEntry.from_key(
            f"redbeat:check_service_{service_id}", app=self.celery_app
        )
        entry.delete()
