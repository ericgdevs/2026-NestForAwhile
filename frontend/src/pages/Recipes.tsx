import { useEffect, useState } from "react";

import {
  addRecipeToList,
  deleteSavedRecipe,
  getRecipes,
  getSavedRecipes,
  saveRecipe,
  type Recipe,
} from "../api/client";
import Icon from "../components/Icon";
import RecipeGroups from "../components/RecipeGroups";

export default function Recipes() {
  const [saved, setSaved] = useState<Recipe[] | null>(null);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [fallback, setFallback] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSavedRecipes()
      .then(setSaved)
      .catch(() => setSaved([]));
    getRecipes()
      .then((result) => {
        setRecipes(result.recipes);
        setFallback(result.used_fallback);
      })
      .catch(() => setRecipes([]))
      .finally(() => setLoading(false));
  }, []);

  async function loadCuisine(cuisine: string) {
    const result = await getRecipes({ cuisine });
    setRecipes((list) => [...list, ...result.recipes.filter((recipe) => !list.some((item) => item.title === recipe.title))]);
  }

  async function remove(recipe: Recipe) {
    await deleteSavedRecipe(recipe.id!);
    setSaved((list) => list?.filter((item) => item.id !== recipe.id) ?? null);
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Recipes</h1>
          <p>Recipes you saved, and new ideas from your cart. Every ingredient is safe for everyone in your household.</p>
        </div>
        {saved && saved.length > 0 && (
          <div className="figure">
            <b>{saved.length}</b>
            <span>saved</span>
          </div>
        )}
      </header>

      <section aria-label="Saved recipes">
        <h2 className="panel-title" style={{ marginBottom: "1rem" }}>
          Saved recipes
        </h2>
        {saved === null ? (
          <p className="empty">Loading your saved recipes…</p>
        ) : saved.length === 0 ? (
          <p className="panel empty">
            <strong>No saved recipes yet.</strong>
            <span>Scan a product and tap Save on a recipe you like.</span>
          </p>
        ) : (
          <RecipeGroups actions={{ onAddToList: addRecipeToList, onDelete: remove }} recipes={saved} />
        )}
      </section>

      <section aria-label="Ideas from your cart" style={{ marginTop: "2rem" }}>
        <h2 className="panel-title" style={{ marginBottom: "1rem" }}>
          Ideas from your cart
        </h2>
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
          <RecipeGroups actions={{ onSave: saveRecipe, onAddToList: addRecipeToList }} loadCuisine={loadCuisine} recipes={recipes} />
        )}
      </section>
    </main>
  );
}
