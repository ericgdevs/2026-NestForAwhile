"""Tables from specs/001-mtg-warehouse-system/data-model.md. Official field names are kept exactly."""
from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.crypto import EncryptedText


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, Enum):
    CLIENT = "Client"
    VOLUNTEER = "Volunteer"
    STAFF = "Warehouse Staff"
    MANAGER = "Warehouse Manager"
    DIRECTOR = "Director"


class EnrollmentStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class QueueStatus(str, Enum):
    WAITING = "waiting"
    READY = "ready"
    CLAIMED = "claimed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# --- identity and profile ---

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(EncryptedText, nullable=False))
    email_hash: str = Field(unique=True, index=True)
    password_hash: str
    role: Role
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class DietaryTier(SQLModel, table=True):
    __tablename__ = "dietary_tiers"
    Dietary_Tier_ID: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str = ""


class ClientProfile(SQLModel, table=True):
    __tablename__ = "clients"
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    name: str = Field(sa_column=Column(EncryptedText, nullable=False))
    Household_Size: int = Field(ge=1)
    Client_Enrollment_Status: EnrollmentStatus
    Dietary_Tier_ID: int | None = Field(default=None, foreign_key="dietary_tiers.Dietary_Tier_ID")
    created_at: datetime = Field(default_factory=utcnow)


class DietaryProfile(SQLModel, table=True):
    __tablename__ = "dietary_profiles"
    client_id: int = Field(foreign_key="clients.user_id", primary_key=True)
    restrictions: str | None = Field(default=None, sa_column=Column(EncryptedText))
    allergies: str | None = Field(default=None, sa_column=Column(EncryptedText))
    preferences: str | None = Field(default=None, sa_column=Column(EncryptedText))
    updated_at: datetime = Field(default_factory=utcnow)


class ClinicalRule(SQLModel, table=True):
    __tablename__ = "clinical_rules"
    id: int | None = Field(default=None, primary_key=True)
    Dietary_Tier_ID: int = Field(foreign_key="dietary_tiers.Dietary_Tier_ID")
    restriction: str
    nutrient: str | None = None
    max_value: float | None = None
    excluded_allergen: str | None = None
    is_placeholder: bool = True


class Visit(SQLModel, table=True):
    __tablename__ = "visits"
    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.user_id")
    session_id: int | None = Field(default=None, foreign_key="shopping_sessions.id")
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
    pounds_distributed: float | None = None


# --- sessions, capacity, queue ---

class ShoppingSession(SQLModel, table=True):
    __tablename__ = "shopping_sessions"
    id: int | None = Field(default=None, primary_key=True)
    Shopping_Session_Token: str = Field(unique=True, index=True)
    client_id: int = Field(foreign_key="clients.user_id")
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: datetime | None = None


class CapacitySettings(SQLModel, table=True):
    __tablename__ = "capacity_settings"
    id: int = Field(default=1, primary_key=True)
    Max_Floor_Capacity: int = Field(ge=1)
    claim_window_minutes: int = 5
    updated_by: int | None = Field(default=None, foreign_key="users.id")
    updated_at: datetime = Field(default_factory=utcnow)


class QueueEntry(SQLModel, table=True):
    __tablename__ = "queue_entries"
    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.user_id")
    joined_at: datetime = Field(default_factory=utcnow)
    status: QueueStatus = QueueStatus.WAITING
    ready_at: datetime | None = None
    claimed_session_id: int | None = Field(default=None, foreign_key="shopping_sessions.id")


# --- catalog and inventory ---

class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: int | None = Field(default=None, primary_key=True)
    sku: str = Field(unique=True)
    barcode: str = Field(unique=True, index=True)
    name: str
    category: str
    image_url: str | None = None
    serving_size_g: float | None = None
    calories: float | None = None
    sodium_mg: float | None = None
    sugar_g: float | None = None
    added_sugar_g: float | None = None
    sat_fat_g: float | None = None
    fiber_g: float | None = None
    protein_g: float | None = None
    potassium_mg: float | None = None
    phosphorus_mg: float | None = None
    carbs_g: float | None = None
    ingredients_text: str | None = None
    allergens: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    diet_flags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    weight_lb: float | None = None
    source: str = "seed"
    fetched_at: datetime | None = None


class InventoryLocation(SQLModel, table=True):
    __tablename__ = "inventory_locations"
    id: int | None = Field(default=None, primary_key=True)
    aisle: str
    shelf: str
    bin: str


class InventoryLot(SQLModel, table=True):
    __tablename__ = "inventory_lots"
    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    location_id: int | None = Field(default=None, foreign_key="inventory_locations.id")
    quantity: int = Field(ge=0)
    received_at: datetime = Field(default_factory=utcnow)
    expiration_date: date | None = None
    reorder_threshold: int = 0


class InventoryMovement(SQLModel, table=True):
    __tablename__ = "inventory_movements"
    id: int | None = Field(default=None, primary_key=True)
    lot_id: int = Field(foreign_key="inventory_lots.id")
    change: int
    reason: str  # checkout | audit | restock | expired
    ref_id: int | None = None
    created_at: datetime = Field(default_factory=utcnow)


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"
    id: int | None = Field(default=None, primary_key=True)
    lot_id: int | None = Field(default=None, foreign_key="inventory_lots.id")
    product_id: int | None = Field(default=None, foreign_key="products.id")
    expected_qty: int
    counted_qty: int = Field(ge=0)
    variance: int
    counted_by: int = Field(foreign_key="users.id")
    counted_at: datetime = Field(default_factory=utcnow)


# --- cart and checkout ---

class Cart(SQLModel, table=True):
    __tablename__ = "carts"
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="shopping_sessions.id", unique=True)


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    cart_id: int = Field(foreign_key="carts.id", primary_key=True)
    product_id: int = Field(foreign_key="products.id", primary_key=True)
    quantity: int = Field(ge=1)
    added_at: datetime = Field(default_factory=utcnow)
    from_recommendation: bool = False


class Recommendation(SQLModel, table=True):
    __tablename__ = "recommendations"
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="shopping_sessions.id")
    product_id: int = Field(foreign_key="products.id")
    suggested_qty: int = Field(ge=1)
    rationale: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class Checkout(SQLModel, table=True):
    __tablename__ = "checkouts"
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="shopping_sessions.id")
    validated_by: int = Field(foreign_key="users.id")
    status: str  # completed | blocked
    total_lb: float | None = None
    completed_at: datetime | None = None


class CheckoutItem(SQLModel, table=True):
    __tablename__ = "checkout_items"
    checkout_id: int = Field(foreign_key="checkouts.id", primary_key=True)
    product_id: int = Field(foreign_key="products.id", primary_key=True)
    lot_id: int | None = Field(default=None, foreign_key="inventory_lots.id")
    quantity: int = Field(ge=1)
    status_at_checkout: str


class Intervention(SQLModel, table=True):
    __tablename__ = "interventions"
    id: int | None = Field(default=None, primary_key=True)
    checkout_id: int = Field(foreign_key="checkouts.id")
    product_id: int = Field(foreign_key="products.id")
    volunteer_id: int = Field(foreign_key="users.id")
    action: str = "removed_item"
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


# --- reporting and AI ---

class DonationSource(SQLModel, table=True):
    __tablename__ = "donors"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    attribution_label: str


class GrantFundingStream(SQLModel, table=True):
    __tablename__ = "grants"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    attribution_label: str


class Report(SQLModel, table=True):
    __tablename__ = "reports"
    id: int | None = Field(default=None, primary_key=True)
    type: str  # donor | grant
    period_start: date
    period_end: date
    generated_by: int = Field(foreign_key="users.id")
    generated_at: datetime = Field(default_factory=utcnow)


class AIRequest(SQLModel, table=True):
    __tablename__ = "ai_requests"
    id: int | None = Field(default=None, primary_key=True)
    kind: str  # recipe | explanation
    model: str
    latency_ms: int | None = None
    valid: bool = False
    used_fallback: bool = False
    created_at: datetime = Field(default_factory=utcnow)
