from sqlalchemy.orm import Session

from app.models import CheckResult, ResultStatus

class CheckResultRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_result_by_service_id(self, service_id: int) -> list:
        return self.db_session.query(CheckResult).filter_by(service_id=service_id).all()

    def create_result(self, service_id: int, status: ResultStatus, response_time: float) -> None:
        check_result = CheckResult(service_id=service_id, status=status, response_time=response_time)
        self.db_session.add(check_result)
        self.db_session.commit()