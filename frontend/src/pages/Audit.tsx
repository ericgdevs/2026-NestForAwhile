import { useState } from "react";
import { apiRequest } from "../api/client";

export default function Audit() {
  const [code, setCode] = useState("");
  const [current, setCurrent] = useState<{ product_id: number; name: string; current_qty: number } | null>(null);
  const [count, setCount] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function lookup() {
    if (!code.trim()) return;
    setLoading(true);
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
      setMessage(`Variance: ${result.variance}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Stock verification</span>
          <h1 className="page-title">Inventory audit</h1>
          <p className="page-subtitle">
            Perform physical counts and record variances directly into inventory logs.
          </p>
        </div>
      </div>

      <section className="ui-card" style={{ maxWidth: "600px", display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div className="form-group">
          <label className="form-label">Scan product</label>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              className="form-input"
              value={code}
              onChange={(event) => setCode(event.target.value)}
              placeholder="SKU or barcode"
            />
            <button className="btn btn-primary" onClick={lookup} disabled={loading}>
              Scan item
            </button>
          </div>
        </div>

        {current && (
          <section
            style={{
              background: "#f8fafc",
              border: "1px solid var(--border-card)",
              borderRadius: "var(--radius-lg)",
              padding: "1.25rem",
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
            }}
          >
            <div>
              <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: "0 0 0.25rem", color: "var(--text-dark)" }}>
                {current.name}
              </h2>
              <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--text-muted)" }}>
                Current count: <strong>{current.current_qty}</strong>
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Actual physical count</label>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  className="form-input"
                  type="number"
                  min="0"
                  value={count}
                  onChange={(event) => setCount(event.target.value)}
                  placeholder="Actual count"
                />
                <button className="btn btn-accent" onClick={submit} disabled={loading || !count}>
                  Confirm
                </button>
              </div>
            </div>
          </section>
        )}

        {message && (
          <p
            role="status"
            style={{
              margin: 0,
              fontSize: "0.9rem",
              fontWeight: 600,
              color: message.includes("Variance") ? "var(--pastel-blue-text)" : "var(--pastel-rose-text)",
              background: message.includes("Variance") ? "var(--pastel-blue-bg)" : "var(--pastel-rose-bg)",
              border: `1px solid ${message.includes("Variance") ? "var(--pastel-blue-border)" : "var(--pastel-rose-border)"}`,
              padding: "0.75rem 1rem",
              borderRadius: "var(--radius-md)",
            }}
          >
            {message}
          </p>
        )}
      </section>
    </main>
  );
}
