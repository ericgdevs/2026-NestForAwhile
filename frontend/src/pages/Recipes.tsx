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
          <article key={recipe.title} className="soft-card p-5">
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
    </main>
  );
}
