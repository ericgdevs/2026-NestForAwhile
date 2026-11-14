import { useState } from "react";

import type { Recipe } from "../api/client";
import Icon from "./Icon";

const DEFAULT_GROUP = "Suggested for you";

// Recipes arrive ranked by the rules-checked API, so the first in each cuisine is its top pick.
export function groupByCuisine(recipes: Recipe[]): [string, Recipe[]][] {
  const groups = new Map<string, Recipe[]>();
  for (const recipe of recipes) {
    const key = recipe.cuisine?.trim() || DEFAULT_GROUP;
    groups.set(key, [...(groups.get(key) ?? []), recipe]);
  }
  return [...groups.entries()];
}

function RecipeCard({ recipe, top }: { recipe: Recipe; top: boolean }) {
  return (
    <article className={`label-panel recipe ${top ? "recipe-top" : ""}`}>
      {top && (
        <p className="pick-bar">
          <Icon name="check" /> Top pick
        </p>
      )}
      <h3>{recipe.title}</h3>
      <hr className="rule-heavy" />
      <h4 className="sr-only">Ingredients</h4>
      <ul className="ingredients">
        {recipe.ingredients.map((ingredient) => (
          <li key={ingredient.name}>
            <span>{ingredient.name}</span>
            {ingredient.location ? (
              <span className="location">
                <Icon name="pin" />
                Aisle {ingredient.location.aisle} · {ingredient.location.shelf} · {ingredient.location.bin}
              </span>
            ) : ingredient.in_cart_or_stock ? (
              <span className="location">In stock</span>
            ) : null}
          </li>
        ))}
      </ul>
      <hr className="rule-mid" />
      <h4 className="sr-only">Steps</h4>
      <ol className="steps">
        {recipe.steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
    </article>
  );
}

export default function RecipeGroups({ recipes }: { recipes: Recipe[] }) {
  const groups = groupByCuisine(recipes);
  const [active, setActive] = useState(0);
  const [, current] = groups[Math.min(active, groups.length - 1)] ?? ["", []];

  return (
    <div>
      {groups.length > 1 && (
        <div className="tabs" role="group" aria-label="Cuisines">
          {groups.map(([cuisine], index) => (
            <button aria-pressed={index === active} key={cuisine} type="button" onClick={() => setActive(index)}>
              {cuisine}
            </button>
          ))}
        </div>
      )}
      <div className="grid grid-auto">
        {current.map((recipe, index) => (
          <RecipeCard key={recipe.title} recipe={recipe} top={index === 0} />
        ))}
      </div>
    </div>
  );
}
