from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.crypto import EncryptedText
from app.db import Base


def utc_now() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(EncryptedText(), nullable=False)
    email_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    client: Mapped[Client | None] = relationship(back_populates="user", uselist=False)


class Client(Base):
    __tablename__ = "clients"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    name: Mapped[str] = mapped_column(EncryptedText(), nullable=False)
    Household_Size: Mapped[int] = mapped_column(Integer, nullable=False)
    Client_Enrollment_Status: Mapped[str] = mapped_column(String(16), nullable=False)
    Dietary_Tier_ID: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="client")
    dietary_profile: Mapped[DietaryProfile | None] = relationship(
        back_populates="client", uselist=False, cascade="all, delete-orphan"
    )
    visits: Mapped[list[Visit]] = relationship(back_populates="client")


class DietaryProfile(Base):
    __tablename__ = "dietary_profiles"

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.user_id"), primary_key=True)
    restrictions: Mapped[str] = mapped_column(EncryptedText(), nullable=False, default="[]")
    allergies: Mapped[str] = mapped_column(EncryptedText(), nullable=False, default="[]")
    preferences: Mapped[str] = mapped_column(EncryptedText(), nullable=False, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    client: Mapped[Client] = relationship(back_populates="dietary_profile")


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.user_id"), nullable=False)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("shopping_sessions.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    pounds_distributed: Mapped[float] = mapped_column(nullable=False, default=0)

    client: Mapped[Client] = relationship(back_populates="visits")


__all__ = ["Client", "DietaryProfile", "User", "Visit"]
