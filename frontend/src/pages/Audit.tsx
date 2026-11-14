import { useState } from "react";

import { apiRequest } from "../api/client";
import Icon from "../components/Icon";

export default function Audit() {
  const [code, setCode] = useState("");
  const [current, setCurrent] = useState<{ product_id: number; name: string; current_qty: number } | null>(null);
  const [count, setCount] = useState("");
  const [variance, setVariance] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function lookup() {
    if (!code.trim()) return;
    setLoading(true);
    setVariance(null);
    try {
      const result = await apiRequest<typeof current>(`/inventory/audit/${encodeURIComponent(code.trim())}`);
      setCurrent(result);
      setMessage("");
    } catch {
      setCurrent(null);
      setMessage("Item not found. Check SKU or barcode.");
    } finally {
      setLoading(false);
    }
  }

  async function submit() {
    if (!current || !count) return;
    setLoading(true);
    try {
      const result = await apiRequest<{ variance: number }>("/inventory/audit", {
        method: "POST",
        body: { product_id: current.product_id, counted_qty: Number(count) },
      });
      setVariance(result.variance);
      setMessage(`Variance: ${result.variance}`);
    } catch {
      setVariance(null);
      setMessage("We couldn't save that count. Check the number and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Inventory audit</h1>
          <p>Scan an item, count what's on the shelf, and record the difference.</p>
        </div>
      </header>

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <section className="panel stack">
          <form
            className="field"
            onSubmit={(event) => {
              event.preventDefault();
              void lookup();
            }}
          >
            <label className="field-label" htmlFor="audit-code">
              1. Scan product
            </label>
            <div className="inline-form">
              <input
                className="input"
                id="audit-code"
                placeholder="SKU or barcode"
                value={code}
                onChange={(event) => setCode(event.target.value)}
              />
              <button className="btn btn-primary" disabled={loading} type="submit">
                Scan item
              </button>
            </div>
          </form>

          {current && (
            <form
              className="field"
              onSubmit={(event) => {
                event.preventDefault();
                void submit();
              }}
            >
              <label className="field-label" htmlFor="audit-count">
                2. Actual physical count
              </label>
              <div className="inline-form">
                <input
                  className="input tabular"
                  id="audit-count"
                  inputMode="numeric"
                  min="0"
                  placeholder="Actual count"
                  type="number"
                  value={count}
                  onChange={(event) => setCount(event.target.value)}
                />
                <button className="btn btn-primary" disabled={loading || !count} type="submit">
                  Confirm
                </button>
              </div>
            </form>
          )}

          {message && variance === null && (
            <p className="alert alert-danger" role="alert">
              <Icon name="alert" />
              {message}
            </p>
          )}
        </section>

        {current ? (
          <article className="label-panel">
            <h2>{current.name}</h2>
            <p className="meta tabular">Product #{current.product_id}</p>
            <hr className="rule-heavy" />
            <dl className="facts">
              <div>
                <dt>Current count</dt>
                <dd>{current.current_qty}</dd>
              </div>
              <div>
                <dt>Actual count</dt>
                <dd>{count || "—"}</dd>
              </div>
            </dl>
            {variance !== null && (
              <>
                <hr className="rule-heavy" />
                <div className="figure" role="status">
                  <b>{variance > 0 ? `+${variance}` : variance}</b>
                  <span>{message}</span>
                </div>
              </>
            )}
          </article>
        ) : (
          <div className="panel empty">
            <Icon name="audit" />
            <strong>No item scanned</strong>
            <span>The current count and variance show here.</span>
          </div>
        )}
      </div>
    </main>
  );
}
