from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String
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


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    barcode: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500))
    serving_size_g: Mapped[float | None] = mapped_column(Float)
    calories: Mapped[float | None] = mapped_column(Float)
    sodium_mg: Mapped[float | None] = mapped_column(Float)
    sugar_g: Mapped[float | None] = mapped_column(Float)
    added_sugar_g: Mapped[float | None] = mapped_column(Float)
    sat_fat_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)
    protein_g: Mapped[float | None] = mapped_column(Float)
    potassium_mg: Mapped[float | None] = mapped_column(Float)
    phosphorus_mg: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    ingredients_text: Mapped[str | None] = mapped_column(String(2000))
    allergens: Mapped[list[str] | None] = mapped_column(JSON)
    diet_flags: Mapped[list[str] | None] = mapped_column(JSON)
    weight_lb: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="seed")
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime)

    inventory_lots: Mapped[list[InventoryLot]] = relationship(back_populates="product")


class InventoryLot(Base):
    __tablename__ = "inventory_lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    aisle: Mapped[str] = mapped_column(String(32), nullable=False)
    shelf: Mapped[str] = mapped_column(String(32), nullable=False)
    bin: Mapped[str] = mapped_column(String(32), nullable=False)
    reorder_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped[Product] = relationship(back_populates="inventory_lots")
    movements: Mapped[list[InventoryMovement]] = relationship(back_populates="lot")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("inventory_lots.id"), nullable=False)
    change: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    ref_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    lot: Mapped[InventoryLot] = relationship(back_populates="movements")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_lots.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    expected_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    counted_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    variance: Mapped[int] = mapped_column(Integer, nullable=False)
    counted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    counted_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


__all__ = [
    "AuditEvent",
    "Client",
    "DietaryProfile",
    "InventoryLot",
    "InventoryMovement",
    "Product",
    "User",
    "Visit",
]
