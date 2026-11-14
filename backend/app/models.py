from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
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


class ShoppingSession(Base):
    __tablename__ = "shopping_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    Shopping_Session_Token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)

    carts: Mapped[list[Cart]] = relationship(back_populates="session")


class CapacitySetting(Base):
    __tablename__ = "capacity_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    Max_Floor_Capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    claim_window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.user_id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="waiting")
    ready_at: Mapped[datetime | None] = mapped_column(DateTime)
    claimed_session_id: Mapped[int | None] = mapped_column(ForeignKey("shopping_sessions.id"))


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("shopping_sessions.id"), unique=True, nullable=False
    )

    session: Mapped[ShoppingSession] = relationship(back_populates="carts")
    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    from_recommendation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    cart: Mapped[Cart] = relationship(back_populates="items")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("shopping_sessions.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    suggested_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    rationale: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class Checkout(Base):
    __tablename__ = "checkouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("shopping_sessions.id"), nullable=False)
    validated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    total_lb: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class CheckoutItem(Base):
    __tablename__ = "checkout_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checkout_id: Mapped[int] = mapped_column(ForeignKey("checkouts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    lot_id: Mapped[int] = mapped_column(ForeignKey("inventory_lots.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status_at_checkout: Mapped[str] = mapped_column(String(16), nullable=False)


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checkout_id: Mapped[int] = mapped_column(ForeignKey("checkouts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    volunteer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


__all__ = [
    "AuditEvent",
    "CapacitySetting",
    "Cart",
    "CartItem",
    "Client",
    "Checkout",
    "CheckoutItem",
    "DietaryProfile",
    "Intervention",
    "InventoryLot",
    "InventoryMovement",
    "Product",
    "QueueEntry",
    "Recommendation",
    "ShoppingSession",
    "User",
    "Visit",
]
