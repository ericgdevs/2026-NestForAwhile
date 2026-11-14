import { useEffect, useState } from "react";

import { getRecipes, type Recipe } from "../api/client";

export default function Recipes() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [fallback, setFallback] = useState(false);

  useEffect(() => {
    getRecipes()
      .then((result) => {
        setRecipes(result.recipes);
        setFallback(result.used_fallback);
      })
      .catch(() => setRecipes([]));
  }, []);

  return (
    <main className="space-y-6">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-stone-500">From your basket</p>
        <h1 className="display-title mt-3">Easy<br />recipes.</h1>
      </div>
        {fallback && (
          <p className="rounded-2xl bg-[#fff0df] p-3 text-sm text-[#8d4a2d]">
            We used our rules-only recipe fallback while the recipe assistant was unavailable.
          </p>
        )}
        {recipes.map((recipe) => (
          <article key={recipe.title} className="soft-card p-5 sm:p-6">
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-xl font-semibold tracking-tight">{recipe.title}</h2>
              <span className="pill shrink-0 text-xs font-bold text-stone-600">From your basket</span>
            </div>
            <h3 className="mt-6 text-xs font-bold uppercase tracking-[0.16em] text-stone-500">Ingredients</h3>
            <ul className="mt-3 flex flex-wrap gap-2">
              {recipe.ingredients.map((ingredient) => <li className="rounded-full bg-[#f7f1e9] px-3 py-1.5 text-sm" key={ingredient.name}>{ingredient.name}</li>)}
            </ul>
            <h3 className="mt-6 text-xs font-bold uppercase tracking-[0.16em] text-stone-500">Steps</h3>
            <ol className="mt-3 space-y-2 pl-5 text-stone-600">
              {recipe.steps.map((step) => <li key={step}>{step}</li>)}
            </ol>
          </article>
        ))}
    </main>
  );
}
