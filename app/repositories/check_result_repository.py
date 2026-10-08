from sqlalchemy import func, select

from app.models import CheckResult, ResultStatus

from .base_repository import BaseRepository

MAX_RESULTS_PER_PAGE = 100


class CheckResultRepository(BaseRepository):
    def get_result_by_service_id(
        self,
        service_id: int,
        page: int = 1,
        per_page: int = MAX_RESULTS_PER_PAGE,
    ) -> list[CheckResult]:
        per_page = min(per_page, MAX_RESULTS_PER_PAGE)
        results = (
            self.db_session.query(CheckResult)
            .filter_by(service_id=service_id)
            .order_by(CheckResult.created_at.desc(), CheckResult.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        for result in results:
            self.db_session.expunge(result)
        return results

    def get_last_results(self, service_ids: list[int]) -> dict[int, CheckResult]:
        """Latest result of each service, in one query: {service_id: result}.

        Services without results are absent from the dict. "Latest" uses the same
        order as get_result_by_service_id: created_at, then id on a tie.
        """
        if not service_ids:
            return {}

        ranked = (
            select(
                CheckResult.id,
                func.row_number()
                .over(
                    partition_by=CheckResult.service_id,
                    order_by=(CheckResult.created_at.desc(), CheckResult.id.desc()),
                )
                .label("rank"),
            )
            .where(CheckResult.service_id.in_(service_ids))
            .subquery()
        )
        results = (
            self.db_session.query(CheckResult)
            .join(ranked, CheckResult.id == ranked.c.id)
            .filter(ranked.c.rank == 1)
            .all()
        )
        for result in results:
            self.db_session.expunge(result)
        return {result.service_id: result for result in results}

    def create_result(
        self,
        service_id: int,
        status: ResultStatus,
        response_time: float,
        is_db_transaction: bool = False,
    ) -> CheckResult:
        check_result = CheckResult(
            service_id=service_id, status=status, response_time=response_time
        )
        self.db_session.add(check_result)

        self.db_flush_or_commit(is_db_transaction)

        self.db_session.expunge(check_result)
        return check_result

    def delete_result(
        self, result_id: int, service_id: int, is_db_transaction: bool = False
    ) -> bool:
        result = (
            self.db_session.query(CheckResult)
            .filter_by(id=result_id, service_id=service_id)
            .first()
        )
        if result is None:
            return False

        self.db_session.delete(result)

        self.db_flush_or_commit(is_db_transaction)

        return True

    def delete_results_by_service_id(
        self, service_id: int, is_db_transaction: bool = False
    ) -> int:
        deleted = (
            self.db_session.query(CheckResult).filter_by(service_id=service_id).delete()
        )

        self.db_flush_or_commit(is_db_transaction)

        return deleted
