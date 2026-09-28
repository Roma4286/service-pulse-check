from unittest.mock import create_autospec

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.operations.errors import UsernameAlreadyTakenError, UserPersistenceError
from app.operations.register_user import RegisterUser, RegisterUserDTO
from app.repositories.user_repository import UserRepository
from factories import make_user


def test_register_user_persists_user(session):
    register_user = RegisterUser(user_repository=UserRepository(session))

    user = register_user(dto=RegisterUserDTO(username="alice", password="secret"))
    session.rollback()

    assert user.id is not None
    assert user.username == "alice"
    assert user.check_password("secret")
    assert session.query(User).filter_by(username="alice").count() == 1


def test_register_user_with_taken_username_raises(session):
    make_user(session, username="alice")
    session.commit()
    register_user = RegisterUser(user_repository=UserRepository(session))

    with pytest.raises(UsernameAlreadyTakenError) as exc_info:
        register_user(dto=RegisterUserDTO(username="alice", password="other"))

    assert exc_info.value.context == {"username": "alice"}
    assert isinstance(exc_info.value.__cause__, IntegrityError)
    assert session.query(User).count() == 1


def test_register_user_wraps_unexpected_error():
    user_repository = create_autospec(UserRepository, instance=True)
    user_repository.create_new_user.side_effect = RuntimeError("db is down")
    register_user = RegisterUser(user_repository=user_repository)

    with pytest.raises(UserPersistenceError) as exc_info:
        register_user(dto=RegisterUserDTO(username="alice", password="secret"))

    assert exc_info.value.context == {"username": "alice"}
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    user_repository.db_rollback.assert_called_once()
