from pydantic import BaseModel, Field, field_validator

from app.models import EnrollmentStatus, QueueStatus, Role
from app.rules.matrix import load_matrix


class LoginRequest(BaseModel):
    email: str
    password: str


class QueueState(BaseModel):
    status: QueueStatus
    position: int | None = None
    message: str = ""


class LoginResult(BaseModel):
    role: Role
    Shopping_Session_Token: str | None = None
    queue: QueueState | None = None


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


class DietaryProfileWrite(BaseModel):
    """Client-editable fields; Dietary_Tier_ID is server-assigned and ignored if sent."""

    restrictions: list[str] = []
    allergies: list[str] = []
    preferences: list[str] = []

    @field_validator("restrictions", "allergies")
    @classmethod
    def only_supported_options(cls, values: list[str]) -> list[str]:
        unknown = [v for v in values if v not in load_matrix()["restrictions"]]
        if unknown:
            raise ValueError(f"Unsupported option: {', '.join(unknown)}")
        return list(dict.fromkeys(values))

    @field_validator("preferences")
    @classmethod
    def clean_preferences(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(v.strip()[:100] for v in values if v.strip()))


class RecommendationRead(BaseModel):
    product_id: int
    name: str
    suggested_qty: int = Field(ge=1)
    rationale: str
    status: str  # Approved | Capped, never Restricted


class ClientRead(BaseModel):
    name: str | None = None
    Household_Size: int | None = Field(default=None, ge=1)
    Client_Enrollment_Status: EnrollmentStatus | None = None
    profile: DietaryProfileRead | None = None
