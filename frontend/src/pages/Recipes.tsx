import { useEffect, useState } from "react";

import { getRecipes, type Recipe } from "../api/client";
import Icon from "../components/Icon";
import RecipeGroups from "../components/RecipeGroups";

export default function Recipes() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [fallback, setFallback] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRecipes()
      .then((result) => {
        setRecipes(result.recipes);
        setFallback(result.used_fallback);
      })
      .catch(() => setRecipes([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Recipe ideas</h1>
          <p>Built from your cart and what's on the shelves today. Every ingredient is checked against your dietary choices.</p>
        </div>
      </header>

      {fallback && (
        <p className="alert alert-info" style={{ marginBottom: "1rem" }}>
          <Icon name="alert" />
          We used our rules-only recipe fallback while the recipe assistant was unavailable.
        </p>
      )}

      {loading ? (
        <p className="empty">Matching recipes to your cart and today's stock…</p>
      ) : recipes.length === 0 ? (
        <div className="panel empty">
          <Icon name="recipes" />
          <strong>No recipes available yet.</strong>
          <span>Add items to your cart to get recipe ideas.</span>
        </div>
      ) : (
        <RecipeGroups recipes={recipes} />
      )}
    </main>
  );
}
