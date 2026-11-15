import type { ParsedLine } from "../api/client";
import Icon from "./Icon";
import NotForLine from "./NotForLine";
import { StatusBadge } from "./StatusBadge";

export type ReviewRow = ParsedLine & { keep: boolean };

type Props = {
  rows: ReviewRow[];
  onChange: (rows: ReviewRow[]) => void;
  /** Called when the client finishes editing a row's text, so it can be matched again. */
  onRecheck: (index: number, text: string) => void;
  onConfirm: () => void;
};

/** One row per catalog product: when two lines matched the same one, keep the first and keep it if either was kept. */
export function mergeByProduct(rows: ReviewRow[]): ReviewRow[] {
  const merged: ReviewRow[] = [];
  for (const row of rows) {
    const twin = row.product_id === null ? undefined : merged.find((other) => other.product_id === row.product_id);
    if (twin) twin.keep = twin.keep || row.keep;
    else merged.push({ ...row });
  }
  return merged;
}

export const NOT_STOCKED = " — not stocked today";

/** What goes on the list: a stocked product as itself, anything else as a plain note with no safety status. */
export function listEntry(row: ReviewRow) {
  if (row.product_id !== null) return { text: row.text, product_id: row.product_id };
  const text = row.text.endsWith(NOT_STOCKED) ? row.text : row.text.slice(0, 120 - NOT_STOCKED.length) + NOT_STOCKED;
  return { text, product_id: null, note: true };
}

// Review step: nothing reaches the shopping list until the client confirms these rows.
export default function ListReview({ rows, onChange, onRecheck, onConfirm }: Props) {
  const update = (index: number, patch: Partial<ReviewRow>) =>
    onChange(rows.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  const kept = rows.filter((row) => row.keep).length;

  return (
    <div className="stack" aria-label="Review your list">
      <ul className="ingredients">
        {rows.map((row, index) => (
          <li className="stack" key={index} style={{ gap: "0.5rem" }}>
            <div className="row">
              <input
                aria-label={`Keep ${row.text}`}
                checked={row.keep}
                type="checkbox"
                onChange={() => update(index, { keep: !row.keep })}
              />
              <input
                aria-label={`Item ${index + 1}`}
                className="input"
                defaultValue={row.text}
                key={row.text}
                onBlur={(event) => event.target.value.trim() !== row.text && onRecheck(index, event.target.value.trim())}
              />
              <button
                aria-label={`Remove ${row.text}`}
                className="btn btn-secondary"
                type="button"
                onClick={() => onChange(rows.filter((_, i) => i !== index))}
              >
                Remove
              </button>
            </div>
            {row.name && row.name !== row.text && <span className="panel-sub">We matched: {row.name}</span>}
            {row.status ? (
              <StatusBadge status={row.status} />
            ) : (
              <span className="alert alert-info">
                <Icon name="alert" />
                We don't carry this today. It will go on your list as a note.
              </span>
            )}
            <NotForLine notFor={row.not_for} />
            {row.status === "Restricted" && (
              <div className="stack" style={{ gap: "0.5rem" }}>
                <p className="alert alert-warn" role="alert">
                  <Icon name="stop" />
                  This isn't recommended for anyone in your household.
                </p>
                {row.swaps?.length ? (
                  row.swaps.map((swap) => (
                    <button
                      className="btn btn-secondary"
                      key={swap.product_id}
                      type="button"
                      onClick={() =>
                        update(index, {
                          text: swap.name,
                          name: swap.name,
                          product_id: swap.product_id,
                          status: swap.status,
                          not_for: swap.not_for,
                          location: { aisle: swap.aisle, shelf: swap.shelf, bin: swap.bin },
                          swaps: [],
                        })
                      }
                    >
                      Use {swap.name} instead ({swap.status}) · Aisle {swap.aisle} · Shelf {swap.shelf} · Bin {swap.bin}
                    </button>
                  ))
                ) : (
                  <p className="panel-sub">There's no safer swap in stock today. A volunteer can help you find one.</p>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
      <button className="btn btn-primary" disabled={!kept} type="button" onClick={onConfirm}>
        Add {kept} to my list
      </button>
    </div>
  );
}
