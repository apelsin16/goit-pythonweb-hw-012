from typing import Literal

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.repository.users import UserRepository
from src.database.models import User, UserRole
from src.schemas import UserCreate


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def user_repo(mock_session):
    return UserRepository(mock_session)


@pytest.fixture
def user_create_data():
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="hashedpassword",
        role=UserRole.USER
    )


@pytest.mark.asyncio
async def test_create_user(user_repo, user_create_data, mock_session):
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    user = await user_repo.create_user(user_create_data, avatar="http://avatar.com/avatar.png")

    assert user.username == user_create_data.username
    assert user.email == user_create_data.email
    assert user.avatar == "http://avatar.com/avatar.png"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email_found(user_repo, mock_session):
    email = "test@example.com"
    fake_user = User(id=1, email=email)

    # Мокаємо результат, який повертає session.execute()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repo.get_user_by_email(email)

    assert result == fake_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_repo, mock_session):
    email = "notfound@example.com"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repo.get_user_by_email(email)

    assert result is None
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_confirmed_email(mock_session, user_repo):
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.confirmed = False

    user_repo.get_user_by_email = AsyncMock(return_value=mock_user)

    await user_repo.confirmed_email("test@example.com")

    assert mock_user.confirmed is True
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_avatar_url(mock_session, user_repo):
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.avatar = "old_url.jpg"

    user_repo.get_user_by_email = AsyncMock(return_value=mock_user)

    result = await user_repo.update_avatar_url("test@example.com", "new_url.jpg")

    assert result.avatar == "new_url.jpg"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_user)
