from app.models import CheckResult, ResultStatus
from app.extentions import db

class CheckResultRepository:
    def get_result_by_service_id(self, service_id: int) -> list:
        return db.session.query(CheckResult).filter_by(service_id=service_id).all()

    def create_result(self, service_id: int, status: ResultStatus, response_time: float) -> None:
        check_result = CheckResult(service_id=service_id, status=status, response_time=response_time)
        db.session.add(check_result)
        db.session.commit()