import { useEffect, useState } from "react";

import {
  addToShoppingList,
  deleteListLine,
  getShoppingList,
  parseShoppingList,
  scanProduct,
  tickListLine,
  type ListLine,
} from "../api/client";
import BarcodeScanner from "../components/BarcodeScanner";
import Icon from "../components/Icon";
import ListReview, { listEntry, mergeByProduct, type ReviewRow } from "../components/ListReview";
import NotForLine from "../components/NotForLine";
import { resizeToBase64Jpeg } from "../lib/resizeImage";
import { StatusBadge } from "../components/StatusBadge";

const RED_CONFIRM = "This isn't recommended for anyone in your household. Add it anyway?";

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
  const [text, setText] = useState("");
  const [suggestions, setSuggestions] = useState<ReviewRow[]>([]);
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
      setSuggestions(mergeByProduct(lines.map((line) => ({ ...line, keep: true }))));
      if (!lines.length) setMessage("We didn't find any items. Try typing one per line.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "We couldn't read that list.");
    } finally {
      setBusy(false);
    }
  }

  async function readPhoto(file: File) {
    setBusy(true);
    setMessage("");
    try {
      await parse({ image_base64: await resizeToBase64Jpeg(file), media_type: "image/jpeg" });
    } catch {
      setMessage("We couldn't open that image. Try a JPG or PNG, or type your list instead.");
      setBusy(false);
    }
  }

  // Scan to add: same safety check as the Scan page, then the same review step.
  async function scanToAdd(code: string) {
    setMessage("");
    try {
      const scan = await scanProduct(code);
      // Stock and swaps come from the same matching as a typed list; unmatched means a plain note.
      const { lines } = scan.product_id ? await parseShoppingList({ text: scan.name }) : { lines: [] };
      const found = lines.find((line) => line.product_id === scan.product_id);
      const row = found ?? { text: scan.name, product_id: null, name: null, status: null, location: null };
      setSuggestions((rows) => mergeByProduct([...rows, { ...row, keep: true }]));
    } catch {
      setMessage("We couldn't find that product. Try again or type it instead.");
    }
  }

  async function recheck(index: number, value: string) {
    if (!value) return;
    try {
      const { lines } = await parseShoppingList({ text: value });
      const found = lines[0];
      if (found) setSuggestions((rows) => mergeByProduct(rows.map((row, i) => (i === index ? { ...found, keep: row.keep } : row))));
    } catch {
      setMessage("We couldn't check that item. Try again.");
    }
  }

  async function addKept() {
    const kept = suggestions.filter((line) => line.keep);
    if (!kept.length) return;
    if (kept.some((line) => line.status === "Restricted") && !window.confirm(RED_CONFIRM)) return;
    const list = await addToShoppingList(kept.map(listEntry));
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
              <Icon name="upload" />
              Upload photo
              <input
                accept="image/*"
                className="sr-only"
                type="file"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  event.target.value = "";
                  if (file) void readPhoto(file);
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
          <span className="field-label">Scan to add</span>
          <BarcodeScanner onDetected={(code) => void scanToAdd(code)} />
          {suggestions.length > 0 && (
            <ListReview rows={suggestions} onChange={setSuggestions} onConfirm={() => void addKept()} onRecheck={(i, v) => void recheck(i, v)} />
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
