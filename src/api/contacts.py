from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.database.db import get_db
from src.database.models import User
from src.repository.contacts import ContactRepository
from src.services.auth import get_current_user
from src.services.contacts import ContactService
from src.schemas import ContactRead, ContactCreate, ContactUpdate

router = APIRouter()


@router.get("/", response_model=List[ContactRead])
async def contact_read(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    contact_service = ContactService(db)
    return await contact_service.get_contacts(user, skip, limit)


@router.post("/", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def contact_create(
        contact_data: ContactCreate,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    contact_service = ContactService(db)
    return await contact_service.create_contact(contact_data, user)


@router.get("/search", response_model=List[ContactRead])
async def search_contacts(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    contact_repo = ContactRepository(db)
    return await contact_repo.search_contacts(user, first_name, last_name, email)


@router.get("/birthday-soon", response_model=List[ContactRead])
async def get_contacts_birthday_soon(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    contact_repo = ContactRepository(db)
    return await contact_repo.get_contacts_birthday_soon(user)


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    contact_repo = ContactRepository(db)
    contact = await contact_repo.get_contact(contact_id, user)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactRead)
async def contact_update(
        contact_id: int,
        contact_data: ContactUpdate,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)):
    contact_service = ContactService(db)
    return await contact_service.update_contact(contact_id, contact_data, user)


@router.delete("/{contact_id}", response_model=ContactRead)
async def contact_delete(
        contact_id: int,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    contact_service = ContactService(db)
    return await contact_service.delete_contact(contact_id, user)
