import { useEffect, useState } from "react";

import {
  addToShoppingList,
  deleteListLine,
  getShoppingList,
  parseShoppingList,
  tickListLine,
  type ListLine,
  type ParsedLine,
} from "../api/client";
import Icon from "../components/Icon";
import NotForLine from "../components/NotForLine";
import { StatusBadge } from "../components/StatusBadge";

function readAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

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
        <span className="tag">{line.source === "recipe" && line.recipe ? `For: ${line.recipe.title}` : "You added"}</span>
      </div>
      <NotForLine notFor={line.not_for} />
      {line.recipe && (
        <details className="list-recipe">
          <summary>Open recipe: {line.recipe.title}</summary>
          <ol className="steps">
            {line.recipe.steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </details>
      )}
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
  const [text, setText] = useState("");
  const [suggestions, setSuggestions] = useState<(ParsedLine & { keep: boolean })[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getShoppingList()
      .then((list) => setItems(list.items))
      .catch(() => setItems([]));
  }, []);

  async function parse(input: Parameters<typeof parseShoppingList>[0]) {
    setBusy(true);
    setMessage("");
    try {
      const { lines } = await parseShoppingList(input);
      setSuggestions(lines.map((line) => ({ ...line, keep: true })));
      if (!lines.length) setMessage("We didn't find any items. Try typing one per line.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "We couldn't read that list.");
    } finally {
      setBusy(false);
    }
  }

  async function addKept() {
    const kept = suggestions.filter((line) => line.keep);
    if (!kept.length) return;
    const list = await addToShoppingList(kept.map((line) => ({ text: line.text, product_id: line.product_id })));
    setItems(list.items);
    setSuggestions([]);
    setText("");
  }

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
          <label className="field">
            <span className="field-label">Type or paste your list</span>
            <textarea
              className="input list-input"
              placeholder={"black beans\noats\nlow-sodium soup"}
              rows={4}
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
          <div className="row" style={{ justifyContent: "flex-start", flexWrap: "wrap" }}>
            <button className="btn btn-primary" disabled={busy || !text.trim()} type="button" onClick={() => void parse({ text })}>
              Find these items
            </button>
            <label className="btn btn-secondary">
              <Icon name="camera" />
              Photo of a list
              <input
                accept="image/*"
                capture="environment"
                className="sr-only"
                type="file"
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (file) await parse({ image_base64: await readAsBase64(file), media_type: file.type || "image/jpeg" });
                  event.target.value = "";
                }}
              />
            </label>
          </div>
          {busy && <p className="panel-sub">Reading your list…</p>}
          {message && (
            <p className="alert alert-info" role="status">
              <Icon name="alert" />
              {message}
            </p>
          )}
          {suggestions.length > 0 && (
            <div className="stack" aria-label="Matches">
              <ul className="ingredients">
                {suggestions.map((line, index) => (
                  <li key={`${line.text}-${index}`}>
                    <label className="list-tick">
                      <input
                        checked={line.keep}
                        type="checkbox"
                        onChange={() =>
                          setSuggestions((all) => all.map((item, i) => (i === index ? { ...item, keep: !item.keep } : item)))
                        }
                      />
                      <span>
                        {line.name ?? line.text}
                        {!line.product_id && <span className="panel-sub"> (we don't carry this)</span>}
                      </span>
                    </label>
                    {line.status && <StatusBadge status={line.status} />}
                  </li>
                ))}
              </ul>
              <button className="btn btn-primary" type="button" onClick={() => void addKept()}>
                Add {suggestions.filter((line) => line.keep).length} to my list
              </button>
            </div>
          )}
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
