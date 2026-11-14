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
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-3xl space-y-5">
        <h1 className="text-2xl font-semibold">Recipes</h1>
        {fallback && (
          <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
            We used our rules-only recipe fallback while the recipe assistant was unavailable.
          </p>
        )}
        {recipes.map((recipe) => (
          <article key={recipe.title} className="rounded-xl bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold">{recipe.title}</h2>
            <h3 className="mt-4 font-medium">Ingredients</h3>
            <ul className="list-disc pl-5">
              {recipe.ingredients.map((ingredient) => <li key={ingredient.name}>{ingredient.name}</li>)}
            </ul>
            <h3 className="mt-4 font-medium">Steps</h3>
            <ol className="list-decimal pl-5">
              {recipe.steps.map((step) => <li key={step}>{step}</li>)}
            </ol>
          </article>
        ))}
      </div>
    </main>
  );
}
