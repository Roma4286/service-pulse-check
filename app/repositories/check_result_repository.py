from app.models import CheckResult, ResultStatus
from .base_repository import BaseRepository

class CheckResultRepository(BaseRepository):
    def get_result_by_service_id(self, service_id: int) -> list[CheckResult]:
        results = self.db_session.query(CheckResult).filter_by(service_id=service_id).all()
        for result in results:
            self.db_session.expunge(result)
        return results

    def create_result(self, service_id: int, status: ResultStatus, response_time: float, is_db_transaction: bool = False) -> CheckResult:
        check_result = CheckResult(service_id=service_id, status=status, response_time=response_time)
        self.db_session.add(check_result)

        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        self.db_session.expunge(check_result)
        return check_result

    def delete_result(self, result_id: int, service_id: int, is_db_transaction: bool = False) -> bool:
        result = self.db_session.get(CheckResult, result_id)
        if result is None or result.service_id != service_id:
            return False

        self.db_session.delete(result)

        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        return True

    def delete_results_by_service_id(self, service_id: int, is_db_transaction: bool = False) -> int:
        deleted = self.db_session.query(CheckResult).filter_by(service_id=service_id).delete()

        if not is_db_transaction:
            self.db_session.commit()

        return deleted
