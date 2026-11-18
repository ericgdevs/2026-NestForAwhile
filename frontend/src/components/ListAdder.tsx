import { useState } from "react";

import { addToShoppingList, parseShoppingList, type ListLine } from "../api/client";
import { resizeToBase64Jpeg } from "../lib/resizeImage";
import Icon from "./Icon";
import ListReview, { listEntry, mergeByProduct, type ReviewRow } from "./ListReview";

const RED_CONFIRM = "This isn't recommended for anyone in your household. Add it anyway?";

/** Type or photograph items, review them, then add them; shared by the List page and Home. */
export default function ListAdder({ onAdded }: { onAdded: (items: ListLine[]) => void }) {
  const [text, setText] = useState("");
  const [suggestions, setSuggestions] = useState<ReviewRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

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
    onAdded(list.items);
    setSuggestions([]);
    setText("");
  }

  return (
    <>
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
      {suggestions.length > 0 && (
        <ListReview rows={suggestions} onChange={setSuggestions} onConfirm={() => void addKept()} onRecheck={(i, v) => void recheck(i, v)} />
      )}
    </>
  );
}
