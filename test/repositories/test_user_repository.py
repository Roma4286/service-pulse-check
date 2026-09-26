import pytest
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.repositories.user_repository import UserRepository
from factories import make_user


def test_create_new_user_persists_user(session):
    repository = UserRepository(session)

    user = repository.create_new_user(username="alice", password="secret")

    assert user.id is not None
    assert user.username == "alice"
    assert user.password_hash != "secret"
    assert user.check_password("secret")
    assert session.query(User).filter_by(username="alice").count() == 1


def test_create_new_user_in_transaction_is_not_committed(session):
    repository = UserRepository(session)

    repository.create_new_user(username="alice", password="secret", is_db_transaction=True)
    repository.db_rollback()

    assert session.query(User).count() == 0


def test_get_user_by_id(session):
    repository = UserRepository(session)
    new_user = make_user(session)
    session.expunge_all()

    user = repository.get_user_by_id(new_user.id)

    assert user is not None
    assert user is not new_user
    assert user.id == new_user.id
    assert user.username == new_user.username


def test_get_user_by_id_returns_none_when_missing(session):
    assert UserRepository(session).get_user_by_id(999) is None


def test_get_user_by_username(session):
    repository = UserRepository(session)
    new_user = make_user(session)
    session.expunge_all()

    user = repository.get_user_by_username(new_user.username)

    assert user is not None
    assert user.id == new_user.id
    assert user.username == new_user.username


def test_get_user_by_username_returns_none_when_missing(session):
    assert UserRepository(session).get_user_by_username("nobody") is None


def test_create_two_users_with_different_usernames(session):
    repository = UserRepository(session)

    first_user = repository.create_new_user(username="first_user", password="secret")
    second_user = repository.create_new_user(username="second_user", password="secret")

    assert first_user.id != second_user.id
    assert session.query(User).count() == 2


def test_create_new_user_with_duplicate_username_raises(session):
    repository = UserRepository(session)
    repository.create_new_user(username="alice", password="secret")

    with pytest.raises(IntegrityError):
        repository.create_new_user(username="alice", password="other")
    session.rollback()

    assert session.query(User).count() == 1
