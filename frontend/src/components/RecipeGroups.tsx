import { useState } from "react";

import { addToShoppingList, type Recipe, type RecipeListResult } from "../api/client";
import Icon, { type IconName } from "./Icon";

const DEFAULT_GROUP = "Suggested for you";
const ALL = "All";
// Offered where the page can ask the API for more; other screens only show cuisines they already have.
export const CUISINES: [string, IconName][] = [
  ["American", "american"],
  ["Mexican", "mexican"],
  ["Italian", "italian"],
  ["Chinese", "chinese"],
  ["Japanese", "japanese"],
  ["Korean", "korean"],
  ["Thai", "thai"],
  ["Vietnamese", "vietnamese"],
  ["Indian", "indian"],
  ["Mediterranean", "mediterranean"],
  ["Middle Eastern", "middleEastern"],
  ["Greek", "greek"],
  ["French", "french"],
  ["Southern", "southern"],
  ["Caribbean", "caribbean"],
  ["African", "african"],
];

function cuisineIcon(cuisine: string): IconName {
  if (cuisine === ALL) return "all";
  return CUISINES.find(([name]) => name.toLowerCase() === cuisine.toLowerCase())?.[1] ?? "recipes";
}

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
  onSave?: (recipe: Recipe) => Promise<RecipeListResult | unknown>;
  onAddToList?: (recipe: Recipe) => Promise<RecipeListResult | unknown>;
  onDelete?: (recipe: Recipe) => Promise<unknown>;
};

const ACTION_LABELS = {
  onSave: ["Save", "Saved"],
  onAddToList: ["Add to list", "On your list"],
  onDelete: ["Delete", "Deleted"],
} as const;

// When the server had nothing to add, "On your list" would overstate what happened.
const NOTHING_TO_ADD = "Nothing to add";

const isListResult = (value: unknown): value is RecipeListResult =>
  typeof value === "object" && value !== null && "added" in value && "blocked" in value;

export function listSummary({ added, in_cart, already_on_list }: RecipeListResult): string {
  const skipped = [in_cart && `${in_cart} already in your cart`, already_on_list && `${already_on_list} already on your list`]
    .filter(Boolean)
    .join(", ");
  const head = added.length
    ? `Added ${added.length} item${added.length === 1 ? "" : "s"} to your list`
    : "Nothing new to add to your list";
  return skipped ? `${head} (${skipped})` : head;
}

function ListConfirmation({ result, recipe }: { result: RecipeListResult; recipe: Recipe }) {
  const [swapped, setSwapped] = useState<string[]>([]);
  return (
    <div className="stack" style={{ gap: "0.5rem" }}>
      <p className={`alert ${result.added.length ? "alert-ok" : "alert-info"}`} role="status">
        <Icon name={result.added.length ? "check" : "list"} />
        <span>
          {listSummary(result)}. <a href="/list">View your list</a>
        </span>
      </p>
      {result.added.length > 0 && (
        <ul className="ingredients">
          {result.added.map((item) => (
            <li key={item.name}>
              <span>{item.name}</span>
              {item.location && (
                <span className="location">
                  <Icon name="pin" />
                  Aisle {item.location.aisle} · {item.location.shelf} · {item.location.bin}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
      {result.blocked.map((blocked) => (
        <div className="alert alert-warn" key={blocked.name} role="alert">
          <Icon name="stop" />
          <div className="stack" style={{ gap: "0.5rem", flex: 1 }}>
            <span>Not added: {blocked.name} isn't recommended for everyone at home.</span>
            {blocked.not_for.length > 0 && (
              <span className="blocked-who">{blocked.not_for.map((who) => `Not for ${who.nickname}: ${who.reason}.`).join(" ")}</span>
            )}
            {blocked.swaps.map((swap) => (
              <button
                className="btn btn-secondary swap-btn"
                disabled={swapped.includes(swap.name)}
                key={swap.product_id}
                type="button"
                onClick={() =>
                  void addToShoppingList([{ text: swap.name, product_id: swap.product_id }], recipe).then(() =>
                    setSwapped((names) => [...names, swap.name]),
                  )
                }
              >
                {swapped.includes(swap.name) && <Icon name="check" />}
                {swapped.includes(swap.name) ? `Added ${swap.name}` : `Add ${swap.name} instead`} · Aisle {swap.aisle} · {swap.shelf} · {swap.bin}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function RecipeButtons({ recipe, actions }: { recipe: Recipe; actions: RecipeActions }) {
  const [done, setDone] = useState<string[]>([]);
  const [failed, setFailed] = useState(false);
  const [result, setResult] = useState<RecipeListResult | null>(null);
  const [nothingAdded, setNothingAdded] = useState(false);
  const keys = (Object.keys(ACTION_LABELS) as (keyof RecipeActions)[]).filter((key) => actions[key]);
  if (!keys.length) return null;

  async function run(key: keyof RecipeActions) {
    setFailed(false);
    try {
      const outcome = await actions[key]!(recipe);
      if (isListResult(outcome)) setResult(outcome);
      if (key === "onAddToList") setNothingAdded(isListResult(outcome) && outcome.added.length === 0);
      setDone((list) => [...list, key]);
    } catch {
      setFailed(true);
    }
  }

  return (
    <div className="stack" style={{ marginTop: "0.75rem", gap: "0.5rem" }}>
      <div className="row" style={{ justifyContent: "flex-start", flexWrap: "wrap" }}>
        {keys.map((key) => {
          const [label, finished] = ACTION_LABELS[key];
          const doneLabel = key === "onAddToList" && nothingAdded ? NOTHING_TO_ADD : finished;
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
      {result && <ListConfirmation recipe={recipe} result={result} />}
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

type Props = {
  recipes: Recipe[];
  actions?: RecipeActions;
  /** Fetches recipes for a cuisine the list doesn't have yet; turns on the full cuisine list. */
  loadCuisine?: (cuisine: string) => Promise<unknown>;
};

export default function RecipeGroups({ recipes, actions = {}, loadCuisine }: Props) {
  const groups = new Map(groupByCuisine(recipes));
  const tabs = [ALL, ...new Set([...(loadCuisine ? CUISINES.map(([name]) => name) : []), ...groups.keys()])];
  const [active, setActive] = useState(ALL);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const current = active === ALL ? recipes : (groups.get(active) ?? []);

  async function pick(cuisine: string) {
    setActive(cuisine);
    setFailed(false);
    if (cuisine === ALL || groups.has(cuisine) || !loadCuisine) return;
    setLoading(true);
    try {
      await loadCuisine(cuisine);
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {(groups.size > 1 || loadCuisine) && (
        <div className="tabs" role="group" aria-label="Cuisines">
          {tabs.map((cuisine) => (
            <button aria-pressed={cuisine === active} key={cuisine} type="button" onClick={() => void pick(cuisine)}>
              <Icon name={cuisineIcon(cuisine)} />
              {cuisine}
            </button>
          ))}
        </div>
      )}
      {loading ? (
        <p className="empty">Finding {active} recipes for your cart…</p>
      ) : failed ? (
        <p className="alert alert-danger" role="alert">
          <Icon name="alert" />
          <span>We couldn't load {active} recipes. Try again.</span>
        </p>
      ) : current.length === 0 ? (
        <p className="panel empty">No {active} recipes for your cart yet.</p>
      ) : (
        <div className="grid grid-auto">
          {current.map((recipe, index) => (
            <RecipeCard actions={actions} key={recipe.id ?? recipe.title} recipe={recipe} top={index === 0} />
          ))}
        </div>
      )}
    </div>
  );
}
