from select import select

from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate
from src.database.models import Contact, User
from typing import Optional, Sequence


class ContactService:
    def __init__(self, db: AsyncSession):
        self.contact_repo = ContactRepository(db)
        self.db = db

    async def get_contacts(self,  user: User, skip: int, limit: int) -> Sequence[Contact]:
        return await self.contact_repo.get_contacts(user, skip, limit)

    async def get_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        return await self.contact_repo.get_contact(contact_id, user)

    async def create_contact(self, contact_data: ContactCreate, user: User) -> Contact:
        return await self.contact_repo.create_contact(contact_data, user)

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user: User) -> Optional[Contact]:
        return await self.contact_repo.update_contact(contact_id, contact_data, user)

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        return await self.contact_repo.delete_contact(contact_id, user)

    async def search_contacts(
            self, user: User, first_name: Optional[str], last_name: Optional[str], email: Optional[str]
    ) -> list:
        return await self.contact_repo.search_contacts(user, first_name, last_name, email)
