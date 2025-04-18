from datetime import datetime, timedelta

from sqlalchemy import select, and_, extract, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate
from typing import List, Optional, Any, Coroutine, Sequence


class ContactRepository:
    """Repository class for managing contact records in the database."""

    def __init__(self, session: AsyncSession):
        self.db = session
        """
        Initialize the ContactRepository with a database session.

        Args:
            session (AsyncSession): The asynchronous SQLAlchemy session.
        """

    async def get_contacts(self, user: User, skip: int, limit: int) -> Sequence[Contact]:
        """
        Retrieve a paginated list of contacts for the given user.

        Args:
            user (User): The user whose contacts are requested.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            Sequence[Contact]: List of contact objects.
        """
        stmt = select(Contact).where(Contact.user_id == user.id).offset(skip).limit(limit)
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Retrieve a specific contact by ID for the given user.

        Args:
            contact_id (int): ID of the contact to retrieve.
            user (User): The user who owns the contact.

        Returns:
            Optional[Contact]: Contact object if found, else None.
        """
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, contact_data: ContactCreate, user: User) -> Contact:
        """
        Create a new contact for the given user.

        Args:
            contact_data (ContactCreate): Data for creating the contact.
            user (User): The user to whom the contact belongs.

        Returns:
            Optional[Contact]: The created contact, or None if creation fails.
        """
        new_contact = Contact(**contact_data.model_dump(exclude_unset=True), user_id=user.id)
        self.db.add(new_contact)
        try:
            await self.db.commit()
            await self.db.refresh(new_contact)
            return new_contact
        except IntegrityError as e:
            await self.db.rollback()
            print(f"DB error while creating contact: {e}")
            return None

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user: User) -> Optional[Contact]:
        """
        Update an existing contact's information.

        Args:
            contact_id (int): ID of the contact to update.
            contact_data (ContactUpdate): New data to update the contact with.
            user (User): The user who owns the contact.

        Returns:
            Optional[Contact]: Updated contact object, or None if update fails or contact not found.
        """
        contact = await self.get_contact(contact_id, user)
        if contact:
            for key, value in contact_data.dict(exclude_unset=True).items():
                setattr(contact, key, value)
            try:
                await self.db.commit()
                await self.db.refresh(contact)
            except IntegrityError as e:
                await self.db.rollback()
                # Можеш залогувати або пробросити далі
                print(f"DB error while updating contact: {e}")
                return None
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Delete a contact by ID for the given user.

        Args:
            contact_id (int): ID of the contact to delete.
            user (User): The user who owns the contact.

        Returns:
            Optional[Contact]: The deleted contact if successful, else None.
        """
        contact = await self.get_contact(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(self, user: User, first_name: Optional[str], last_name: Optional[str],
                              email: Optional[str]):
        """
        Search contacts by first name, last name, or email.

        Args:
            user (User): The user whose contacts are being searched.
            first_name (Optional[str]): First name search query.
            last_name (Optional[str]): Last name search query.
            email (Optional[str]): Email search query.

        Returns:
            List[Contact]: List of matching contacts.
        """
        stmt = select(Contact).where(Contact.user_id == user.id)
        if first_name:
            stmt = stmt.filter(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.filter(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            stmt = stmt.filter(Contact.email.ilike(f"%{email}%"))
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contacts_birthday_soon(self, user: User):
        """
        Retrieve contacts whose birthdays are within the next 7 days.

        Args:
            user (User): The user whose contacts are being checked.

        Returns:
            List[Contact]: List of contacts with upcoming birthdays.
        """
        today = datetime.today()
        seven_days_later = today + timedelta(days=7)

        stmt = select(Contact).where(Contact.user_id == user.id).filter(
            or_(
                and_(
                    extract('month', Contact.birthday) == today.month,
                    extract('day', Contact.birthday) >= today.day
                ),
                and_(
                    extract('month', Contact.birthday) == seven_days_later.month,
                    extract('day', Contact.birthday) <= seven_days_later.day
                )
            )
        )

        result = await self.db.execute(stmt)
        contacts = result.scalars().all()

        if contacts is None:  # Додаємо перевірку
            return []

        return contacts  # Гарантовано повертає список
