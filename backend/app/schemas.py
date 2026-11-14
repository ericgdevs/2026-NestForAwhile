from pydantic import BaseModel, Field

from app.models import EnrollmentStatus, QueueStatus, Role


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    role: Role


class MeResponse(BaseModel):
    user: UserRead
    Client_Enrollment_Status: EnrollmentStatus | None = None
    Household_Size: int | None = Field(default=None, ge=1)
    Dietary_Tier_ID: int | None = None


class LoginResponse(BaseModel):
    Shopping_Session_Token: str


class QueueState(BaseModel):
    status: QueueStatus
    position: int | None = None
    message: str = ""


class CapacityResponse(BaseModel):
    Active_Floor_Shoppers: int
    Max_Floor_Capacity: int
    Queue_Waiting: int


class CartManifestLine(BaseModel):
    product_id: int
    name: str
    quantity: int = Field(ge=1)


class CartResponse(BaseModel):
    Active_Cart_Manifest: list[CartManifestLine]


class DietaryProfileRead(BaseModel):
    restrictions: list[str] = []
    allergies: list[str] = []
    preferences: list[str] = []
    Dietary_Tier_ID: int | None = None


class RecommendationRead(BaseModel):
    product_id: int
    name: str
    suggested_qty: int = Field(ge=1)
    rationale: str
    status: str  # Approved | Capped, never Restricted
