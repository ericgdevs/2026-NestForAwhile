import { useEffect, useState } from "react";

import { deleteListLine, getShoppingList, tickListLine, type ListLine } from "../api/client";
import Icon from "../components/Icon";
import ListAdder from "../components/ListAdder";
import NotForLine from "../components/NotForLine";
import { StatusBadge } from "../components/StatusBadge";

function ListLineRow({ line, onChange }: { line: ListLine; onChange: (items: ListLine[]) => void }) {
  async function tick(ticked: boolean) {
    onChange((await tickListLine(line.id, ticked)).items);
  }

  return (
    <li className={`list-line ${line.ticked ? "list-line-done" : ""}`}>
      <label className="list-tick">
        <input checked={line.ticked} type="checkbox" onChange={(event) => void tick(event.target.checked)} />
        <span>
          <strong>{line.name}</strong>
          {line.name !== line.text && <span className="panel-sub"> ({line.text})</span>}
        </span>
      </label>
      <div className="list-meta">
        {line.location ? (
          <span className="location">
            <Icon name="pin" />
            Aisle {line.location.aisle} · Shelf {line.location.shelf} · Bin {line.location.bin}
          </span>
        ) : (
          <span className="panel-sub">{line.product_id ? "Out of stock today" : "We don't carry this today"}</span>
        )}
        {line.status && <StatusBadge status={line.status} />}
        {line.source === "you" && <span className="tag">You added</span>}
        {line.recipes.map((recipe) => (
          <span className="tag" key={recipe.title}>
            For: {recipe.title}
          </span>
        ))}
      </div>
      <NotForLine notFor={line.not_for} />
      {line.recipes.map((recipe) => (
        <details className="list-recipe" key={recipe.title}>
          <summary>Open recipe: {recipe.title}</summary>
          <ol className="steps">
            {recipe.steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </details>
      ))}
      <button
        aria-label={`Remove ${line.name}`}
        className="btn btn-secondary list-remove"
        type="button"
        onClick={() => void deleteListLine(line.id).then(() => getShoppingList()).then((list) => onChange(list.items))}
      >
        Remove
      </button>
    </li>
  );
}

export default function ShoppingList() {
  const [items, setItems] = useState<ListLine[] | null>(null);

  useEffect(() => {
    getShoppingList()
      .then((list) => setItems(list.items))
      .catch(() => setItems([]));
  }, []);

  const left = items?.filter((line) => !line.ticked).length ?? 0;

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Shopping list</h1>
          <p>Your items and recipe ingredients, in aisle order. Tick each one as it goes in your cart.</p>
        </div>
        {items && (
          <div className="figure">
            <b>{left}</b>
            <span>left to find</span>
          </div>
        )}
      </header>

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <section className="panel stack" aria-label="Add to your list">
          <ListAdder onAdded={setItems} />
        </section>

        <section className="panel" aria-label="Your list">
          {items === null ? (
            <p className="empty">Loading your list…</p>
          ) : items.length === 0 ? (
            <div className="empty">
              <Icon name="list" />
              <strong>Your list is empty.</strong>
              <span>Add your own items, or tap "Add to list" on a recipe.</span>
            </div>
          ) : (
            <ul className="list-lines">
              {items.map((line) => (
                <ListLineRow key={line.id} line={line} onChange={setItems} />
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
