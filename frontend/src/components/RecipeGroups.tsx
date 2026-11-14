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

export type RecipeActions = {
  onSave?: (recipe: Recipe) => Promise<unknown>;
  onAddToList?: (recipe: Recipe) => Promise<unknown>;
  onDelete?: (recipe: Recipe) => Promise<unknown>;
};

const ACTION_LABELS = {
  onSave: ["Save", "Saved"],
  onAddToList: ["Add to list", "On your list"],
  onDelete: ["Delete", "Deleted"],
} as const;

function RecipeButtons({ recipe, actions }: { recipe: Recipe; actions: RecipeActions }) {
  const [done, setDone] = useState<string[]>([]);
  const [failed, setFailed] = useState(false);
  const keys = (Object.keys(ACTION_LABELS) as (keyof RecipeActions)[]).filter((key) => actions[key]);
  if (!keys.length) return null;

  async function run(key: keyof RecipeActions) {
    setFailed(false);
    try {
      await actions[key]!(recipe);
      setDone((list) => [...list, key]);
    } catch {
      setFailed(true);
    }
  }

  return (
    <div className="stack" style={{ marginTop: "0.75rem", gap: "0.5rem" }}>
      <div className="row" style={{ justifyContent: "flex-start", flexWrap: "wrap" }}>
        {keys.map((key) => {
          const [label, doneLabel] = ACTION_LABELS[key];
          const isDone = done.includes(key);
          return (
            <button
              aria-label={`${isDone ? doneLabel : label}: ${recipe.title}`}
              className={`btn ${isDone ? "btn-done" : key === "onAddToList" ? "btn-primary" : "btn-secondary"}`}
              disabled={isDone}
              key={key}
              type="button"
              onClick={() => void run(key)}
            >
              {isDone && <Icon name="check" />}
              {isDone ? doneLabel : label}
            </button>
          );
        })}
      </div>
      {failed && (
        <p className="alert alert-danger" role="alert">
          <Icon name="alert" />
          That didn't work. Please try again.
        </p>
      )}
    </div>
  );
}

function RecipeCard({ recipe, top, actions }: { recipe: Recipe; top: boolean; actions: RecipeActions }) {
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
      <RecipeButtons actions={actions} recipe={recipe} />
    </article>
  );
}

export default function RecipeGroups({ recipes, actions = {} }: { recipes: Recipe[]; actions?: RecipeActions }) {
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
          <RecipeCard actions={actions} key={recipe.id ?? recipe.title} recipe={recipe} top={index === 0} />
        ))}
      </div>
    </div>
  );
}
