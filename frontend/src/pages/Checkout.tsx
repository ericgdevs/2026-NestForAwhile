import { useState } from "react";

import { completeCheckout, validateCheckout } from "../api/client";

export default function Checkout() {
  const [token, setToken] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [receipt, setReceipt] = useState<{ checkout_id: number; total_lb: number } | null>(null);
  const [loading, setLoading] = useState(false);

  async function review() {
    setLoading(true);
    try {
      const result = await validateCheckout(token);
      setErrors(result.errors);
      if (result.valid) setReceipt(null);
    } finally {
      setLoading(false);
    }
  }

  async function complete() {
    setLoading(true);
    try {
      setReceipt(await completeCheckout(token));
      setErrors([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Volunteer verification</span>
          <h1 className="page-title">Checkout</h1>
          <p className="page-subtitle">
            Validate client cart items against clinical dietary rules before completing the visit.
          </p>
        </div>
      </div>

      <section className="ui-card" style={{ maxWidth: "640px", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <label className="form-group">
          <span className="form-label">Shopping session token</span>
          <input
            className="form-input"
            placeholder="Enter or scan session token"
            value={token}
            onChange={(event) => setToken(event.target.value)}
          />
        </label>

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <button className="btn btn-secondary" onClick={() => void review()} disabled={loading || !token.trim()}>
            Review cart
          </button>
          <button className="btn btn-primary" onClick={() => void complete()} disabled={loading || !token.trim()}>
            Complete checkout
          </button>
        </div>

        {errors.length > 0 && (
          <div
            style={{
              background: "var(--pastel-rose-bg)",
              border: "1px solid var(--pastel-rose-border)",
              color: "var(--pastel-rose-text)",
              padding: "1rem 1.25rem",
              borderRadius: "var(--radius-md)",
            }}
          >
            <strong style={{ display: "block", marginBottom: "0.5rem" }}>Checkout needs attention</strong>
            <ul style={{ margin: 0, paddingLeft: "1.25rem", lineHeight: 1.5 }}>
              {errors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {receipt && (
          <div
            style={{
              background: "var(--pastel-green-bg)",
              border: "1px solid var(--pastel-green-border)",
              color: "var(--pastel-green-text)",
              padding: "1.25rem",
              borderRadius: "var(--radius-md)",
              fontWeight: 600,
              fontSize: "1.05rem",
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
            }}
          >
            <span aria-hidden="true">✓</span>
            <span>Receipt #{receipt.checkout_id} · {receipt.total_lb} lb distributed</span>
          </div>
        )}
      </section>
    </main>
  );
}
