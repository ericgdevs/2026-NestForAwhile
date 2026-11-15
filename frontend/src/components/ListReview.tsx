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
                We don't carry this. You can still keep it on your list.
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
