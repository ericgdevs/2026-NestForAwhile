from app.rules.matrix import load_matrix

# Synthetic placeholder tiers until the team confirms the real mapping
TIERS = {
    1: ("General", "No dietary restrictions"),
    2: ("Dietary Preference or Allergy", "Vegetarian, Vegan, Gluten Free, Dairy Free, Nut Allergy"),
    3: ("Condition Managed", "Low Sugar, Low Sodium, Heart Healthy"),
    4: ("Kidney Care", "Kidney Friendly"),
}


def tier_for(restrictions: list[str]) -> int:
    """Strictest (highest) tier among the selected restrictions wins."""
    rules = load_matrix()["restrictions"]
    return max((rules[r]["tier"] for r in restrictions), default=1)
