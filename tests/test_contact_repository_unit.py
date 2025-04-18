from datetime import datetime, timedelta

import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, Contact
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def contact_repository(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def user():
    return User(id=1, username="testuser")


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [Contact(id=1, first_name="test contact", user=user)]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contacts = await contact_repository.get_contacts(skip=0, limit=10, user=user)

    # Assertions
    assert len(contacts) == 1
    assert contacts[0].first_name == "test contact"


@pytest.mark.asyncio
async def test_get_contact(contact_repository, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(id=1, first_name="test contact", user=user)
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contact = await contact_repository.get_contact(contact_id=1, user=user)

    # Assertions
    assert contact is not None
    assert contact.id == 1
    assert contact.first_name == "test contact"


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, user):
    # Arrange
    contact_data = ContactCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="1234567890",
        birthday=datetime(2000, 1, 12),
        extra_info="Test contact"
    )

    # Щоб симулювати commit/refresh
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.add = MagicMock()

    # Act
    result = await contact_repository.create_contact(contact_data=contact_data, user=user)

    # Assert
    assert result is not None
    assert isinstance(result, Contact)
    assert result.first_name == "John"
    assert result.user_id == user.id

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, user):
    contact_data = ContactUpdate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="1234567890",
        birthday=datetime(2000, 1, 12),
        extra_info="New info"
    )

    existing_contact = Contact(
        id=1,
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        phone="0987654321",
        birthday=datetime(1990, 5, 20),
        extra_info="Old info",
        user_id=user.id
    )

    # Мокаємо get_contact, щоб повертав об'єкт Contact
    contact_repository.get_contact = AsyncMock(return_value=existing_contact)

    # Викликаємо функцію
    result = await contact_repository.update_contact(
        contact_id=1, contact_data=contact_data, user=user
    )

    # Перевіряємо результат
    assert result is not None
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.email == "john@example.com"
    assert result.extra_info == "New info"

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(existing_contact)


@pytest.mark.asyncio
async def test_delete_contact(contact_repository, mock_session, user):
    existing_contact = Contact(
        id=1,
        first_name="Test",
        last_name="Contact",
        email="test@example.com",
        user_id=user.id
    )

    # Мокаємо get_contact
    contact_repository.get_contact = AsyncMock(return_value=existing_contact)

    # Викликаємо метод
    result = await contact_repository.delete_contact(contact_id=1, user=user)

    # Перевірки
    assert result is not None
    assert result.id == 1
    mock_session.delete.assert_called_once_with(existing_contact)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_search_contacts_with_all_fields(contact_repository, mock_session, user):
    # Arrange
    query_contacts = [
        Contact(id=1, first_name="Alice", last_name="Doe", email="alice@example.com", user_id=user.id),
        Contact(id=2, first_name="Alicia", last_name="Doe", email="alicia@example.com", user_id=user.id)
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = query_contacts
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await contact_repository.search_contacts(
        user=user,
        first_name="Ali",
        last_name="Doe",
        email="example.com"
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(contact, Contact) for contact in result)
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contacts_birthday_soon(contact_repository, mock_session, user):
    # Arrange
    today = datetime.today()
    in_five_days = today + timedelta(days=5)
    contact_1 = Contact(
        id=1,
        first_name="BirthdaySoon",
        last_name="Person",
        email="soon@example.com",
        phone="123456789",
        birthday=in_five_days,
        user_id=user.id
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact_1]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Act
    result = await contact_repository.get_contacts_birthday_soon(user)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].first_name == "BirthdaySoon"
    mock_session.execute.assert_called_once()
