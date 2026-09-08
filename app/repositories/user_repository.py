
from app.models import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def get_user_by_id(self, id: int) -> User | None:
        user = self.db_session.query(User).filter_by(id=id).first()
        if user is not None:
            self.db_session.expunge(user)
        return user

    def get_user_by_username(self, username: str) -> User | None:
        user = self.db_session.query(User).filter_by(username=username).first()
        if user is not None:
            self.db_session.expunge(user)
        return user

    def create_new_user(self, username: str, password: str, is_db_transaction: bool = False) -> User:
        user = User(username=username, password=password)
        self.db_session.add(user)
        if is_db_transaction:
            self.db_session.flush()
        else:
            self.db_session.commit()

        self.db_session.expunge(user)
        return user

