from sqlalchemy.orm import Session

class BaseRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def db_commit(self) -> None:
        self.db_session.commit()

    def db_flush_or_commit(self, is_db_transaction: bool) -> None:
        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_commit()

    def db_rollback(self) -> None:
        self.db_session.rollback()