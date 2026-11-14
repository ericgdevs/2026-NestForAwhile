import { useRef, useState } from "react";

import { getRecipes, type Recipe } from "../api/client";
import Icon from "./Icon";
import RecipeGroups from "./RecipeGroups";

// Bottom sheet on the client home; recipes load only when opened because each request may call the AI.
export default function RecipeSheet() {
  const [open, setOpen] = useState(false);
  const [recipes, setRecipes] = useState<Recipe[] | null>(null);
  const [fallback, setFallback] = useState(false);
  const [error, setError] = useState(false);
  const requested = useRef(false);

  function toggle() {
    setOpen((value) => !value);
    if (!requested.current) {
      requested.current = true;
      getRecipes()
        .then((result) => {
          setRecipes(result.recipes);
          setFallback(result.used_fallback);
        })
        .catch(() => {
          setRecipes([]);
          setError(true);
        });
    }
  }

  return (
    <section className="sheet" data-open={open} aria-label="Recipe ideas">
      <button aria-controls="recipe-sheet-body" aria-expanded={open} className="sheet-handle" type="button" onClick={toggle}>
        <span style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
          <Icon name="recipes" />
          Recipe ideas from your cart
        </span>
        <Icon name="chevron" />
      </button>
      <div className="sheet-body" id="recipe-sheet-body">
        {recipes === null ? (
          <p className="empty">Matching recipes to your cart and today's stock…</p>
        ) : recipes.length === 0 ? (
          <div className="empty">
            <Icon name="recipes" />
            <strong>{error ? "Recipes are unavailable right now." : "No recipes yet."}</strong>
            <span>Add items to your cart, then open this again.</span>
          </div>
        ) : (
          <div className="stack">
            {fallback && (
              <p className="alert alert-info">
                <Icon name="alert" />
                These are simple ideas from our rules-only fallback while the recipe assistant is unavailable.
              </p>
            )}
            <RecipeGroups recipes={recipes} />
            <a className="btn btn-secondary" href="/recipes">
              See all recipes
            </a>
          </div>
        )}
      </div>
    </section>
  );
}
