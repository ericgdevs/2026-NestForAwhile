"""Synthetic catalog sample. Structure first: extend PRODUCTS toward the 100-product target."""

# expires_in_days is relative to the load date (negative = already expired)
PRODUCTS = [
    {"sku": "SYN-001", "barcode": "990000000011", "name": "Rolled Oats", "category": "Grains",
     "serving_size_g": 40, "calories": 150, "sodium_mg": 0, "sugar_g": 1, "added_sugar_g": 0, "sat_fat_g": 0.5,
     "fiber_g": 4, "protein_g": 5, "potassium_mg": 150, "phosphorus_mg": 130, "carbs_g": 27,
     "ingredients_text": "whole grain oats", "allergens": [], "diet_flags": ["is_vegan"], "weight_lb": 1.0,
     "location": ("A1", "S1", "B1"), "quantity": 40, "expires_in_days": 180, "reorder_threshold": 10},
    {"sku": "SYN-002", "barcode": "990000000028", "name": "Canned Tomato Soup", "category": "Soup",
     "serving_size_g": 245, "calories": 90, "sodium_mg": 700, "sugar_g": 9, "added_sugar_g": 4, "sat_fat_g": 0.5,
     "fiber_g": 2, "protein_g": 2, "potassium_mg": 380, "phosphorus_mg": 40, "carbs_g": 20,
     "ingredients_text": "tomatoes, water, salt", "allergens": [], "diet_flags": ["is_vegan"], "weight_lb": 1.1,
     "location": ("A1", "S2", "B3"), "quantity": 60, "expires_in_days": 365, "reorder_threshold": 15},
    {"sku": "SYN-003", "barcode": "990000000035", "name": "Peanut Butter", "category": "Spreads",
     "serving_size_g": 32, "calories": 190, "sodium_mg": 140, "sugar_g": 3, "added_sugar_g": 1, "sat_fat_g": 3,
     "fiber_g": 2, "protein_g": 7, "potassium_mg": 200, "phosphorus_mg": 110, "carbs_g": 7,
     "ingredients_text": "peanuts, salt", "allergens": ["peanuts"], "diet_flags": ["is_vegan"], "weight_lb": 1.0,
     "location": ("A2", "S1", "B2"), "quantity": 25, "expires_in_days": 4, "reorder_threshold": 10},
    {"sku": "SYN-004", "barcode": "990000000042", "name": "Whole Milk", "category": "Dairy",
     "serving_size_g": 240, "calories": 150, "sodium_mg": 105, "sugar_g": 12, "added_sugar_g": 0, "sat_fat_g": 4.5,
     "fiber_g": 0, "protein_g": 8, "potassium_mg": 350, "phosphorus_mg": 220, "carbs_g": 12,
     "ingredients_text": "milk", "allergens": ["milk"], "diet_flags": ["contains_dairy"], "weight_lb": 2.2,
     "location": ("C1", "S1", "B1"), "quantity": 12, "expires_in_days": -2, "reorder_threshold": 8},
    {"sku": "SYN-005", "barcode": "990000000059", "name": "Whole Wheat Bread", "category": "Bakery",
     "serving_size_g": 43, "calories": 110, "sodium_mg": 180, "sugar_g": 3, "added_sugar_g": 2, "sat_fat_g": 0,
     "fiber_g": 3, "protein_g": 5, "potassium_mg": 120, "phosphorus_mg": 110, "carbs_g": 20,
     "ingredients_text": "whole wheat flour, water, yeast", "allergens": ["wheat"], "diet_flags": ["contains_gluten", "is_vegan"],
     "weight_lb": 1.4, "location": ("B1", "S2", "B1"), "quantity": 30, "expires_in_days": 6, "reorder_threshold": 12},
    {"sku": "SYN-006", "barcode": "990000000066", "name": "Frozen Chicken Breast", "category": "Protein",
     "serving_size_g": 112, "calories": 120, "sodium_mg": 330, "sugar_g": 0, "added_sugar_g": 0, "sat_fat_g": 0.5,
     "fiber_g": 0, "protein_g": 24, "potassium_mg": 300, "phosphorus_mg": 190, "carbs_g": 0,
     "ingredients_text": "chicken breast, water, salt", "allergens": [], "diet_flags": ["contains_meat"], "weight_lb": 3.0,
     "location": ("C2", "S1", "B4"), "quantity": 18, "expires_in_days": 90, "reorder_threshold": 6},
]

DONORS = [{"name": "Synthetic Community Food Co-op", "attribution_label": "Donor A (synthetic)"}]
GRANTS = [{"name": "Synthetic Neighborhood Nutrition Grant", "attribution_label": "Grant A (synthetic)"}]
