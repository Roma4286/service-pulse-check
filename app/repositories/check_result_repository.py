from app.models import CheckResult, ResultStatus
from .base_repository import BaseRepository

class CheckResultRepository(BaseRepository):
    def get_result_by_service_id(self, service_id: int) -> list:
        return self.db_session.query(CheckResult).filter_by(service_id=service_id).all()

    def create_result(self, service_id: int, status: ResultStatus, response_time: float, is_db_transaction: bool = False) -> None:
        check_result = CheckResult(service_id=service_id, status=status, response_time=response_time)
        self.db_session.add(check_result)
    
        if not is_db_transaction:
            self.db_session.commit()

    def db_commit(self) -> None:
        self.db_session.commit()