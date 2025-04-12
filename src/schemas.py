from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime, date
from typing import Optional


# Схема для створення нового контакту (Create Contact)
class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    birthday: datetime
    extra_info: Optional[str] = None

    class Config:
        # Це допомагає використовувати SQLAlchemy моделі для Pydantic
        model_config = ConfigDict(from_attributes=True)


# Схема для читання даних про контакт (Read Contact)
class ContactRead(ContactCreate):
    id: int

    class Config:
        model_config = ConfigDict(from_attributes=True)


# Схема для оновлення контакту (Update Contact)
class ContactUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    birthday: Optional[date]
    extra_info: Optional[str] = None

    class Config:
        model_config = ConfigDict(from_attributes=True)


# Схема користувача
class User(BaseModel):
    id: int
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)


# Схема для запиту реєстрації
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


# Схема для токену
class Token(BaseModel):
    access_token: str
    token_type: str


class RequestEmail(BaseModel):
    email: EmailStr
