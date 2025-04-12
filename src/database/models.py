from datetime import date
from typing import Optional

from sqlalchemy import String, Date, Integer, Column, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String, index=True)
    last_name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String, index=True)
    birthday: Mapped[date] = mapped_column(Date)
    extra_info: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user = relationship('User', backref="contacts")

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=func.now())
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
