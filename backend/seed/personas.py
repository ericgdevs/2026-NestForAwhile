"""Synthetic users and the five patient personas. No real client data."""
from app.models import EnrollmentStatus, Role

# One synthetic user per non-client role
STAFF_USERS = {
    Role.VOLUNTEER: "volunteer@example.test",
    Role.STAFF: "staff@example.test",
    Role.MANAGER: "manager@example.test",
    Role.DIRECTOR: "director@example.test",
}

PERSONAS = [
    {"email": "persona1@example.test", "name": "Persona One", "household_size": 4,
     "status": EnrollmentStatus.ACTIVE, "conditions": ["diabetes", "hypertension"], "extra_restrictions": [], "allergies": []},
    {"email": "persona2@example.test", "name": "Persona Two", "household_size": 1,
     "status": EnrollmentStatus.ACTIVE, "conditions": ["ckd", "diabetes"], "extra_restrictions": [], "allergies": []},
    {"email": "persona3@example.test", "name": "Persona Three", "household_size": 2,
     "status": EnrollmentStatus.ACTIVE, "conditions": ["hypertension"], "extra_restrictions": [], "allergies": []},
    {"email": "persona4@example.test", "name": "Persona Four", "household_size": 6,
     "status": EnrollmentStatus.ACTIVE, "conditions": [], "extra_restrictions": ["Vegan"], "allergies": ["Nut Allergy"]},
    {"email": "persona5@example.test", "name": "Persona Five", "household_size": 3,
     "status": EnrollmentStatus.PENDING, "conditions": [], "extra_restrictions": [], "allergies": []},
]

CLIENT_ROLE_EMAIL = PERSONAS[0]["email"]
