from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.models import User
from app.repositories.user_repository import UserRepository

from .errors import UsernameAlreadyTakenError, UserPersistenceError


@dataclass(frozen=True, slots=True)
class RegisterUserDTO:
    username: str
    password: str


@dataclass(kw_only=True, slots=True)
class RegisterUser:
    user_repository: UserRepository

    def __call__(self, *, dto: RegisterUserDTO) -> User:
        try:
            user = self.user_repository.create_new_user(username=dto.username, password=dto.password)
        except IntegrityError as e:
            self.user_repository.db_rollback()
            raise UsernameAlreadyTakenError(username=dto.username) from e
        except Exception as e:
            self.user_repository.db_rollback()
            raise UserPersistenceError(username=dto.username) from e

        return user
