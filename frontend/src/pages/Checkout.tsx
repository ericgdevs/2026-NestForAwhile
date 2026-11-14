import { useState } from "react";

import { completeCheckout, validateCheckout } from "../api/client";
import Icon from "../components/Icon";

export default function Checkout() {
  const [token, setToken] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [receipt, setReceipt] = useState<{ checkout_id: number; total_lb: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState("");

  async function review() {
    setLoading(true);
    setRequestError("");
    try {
      const result = await validateCheckout(token);
      setErrors(result.errors);
      if (result.valid) setReceipt(null);
    } catch (reason) {
      setRequestError(reason instanceof Error ? reason.message : "We couldn't review this cart.");
    } finally {
      setLoading(false);
    }
  }

  async function complete() {
    setLoading(true);
    setRequestError("");
    try {
      setReceipt(await completeCheckout(token));
      setErrors([]);
    } catch (reason) {
      setRequestError(reason instanceof Error ? reason.message : "We couldn't complete this checkout.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Checkout</h1>
          <p>Enter the client's session token, review the cart against their dietary rules, then complete the visit.</p>
        </div>
      </header>

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <section className="panel stack">
          <div className="field">
            <label className="field-label" htmlFor="session-token">
              Shopping session token
            </label>
            <input
              autoComplete="off"
              className="input tabular"
              id="session-token"
              placeholder="Enter or scan session token"
              value={token}
              onChange={(event) => setToken(event.target.value)}
            />
          </div>
          <div className="row" style={{ justifyContent: "flex-start", flexWrap: "wrap" }}>
            <button className="btn btn-secondary" disabled={loading || !token.trim()} type="button" onClick={() => void review()}>
              Review cart
            </button>
            <button className="btn btn-primary" disabled={loading || !token.trim()} type="button" onClick={() => void complete()}>
              Complete checkout
            </button>
          </div>
          {requestError && (
            <p className="alert alert-danger" role="alert">
              <Icon name="alert" />
              {requestError}. Check the token with the client and try again.
            </p>
          )}
          {errors.length > 0 && (
            <div className="alert alert-danger" role="alert">
              <Icon name="stop" />
              <div>
                <strong>Checkout needs attention</strong>
                <p style={{ fontWeight: 400 }}>Stop here. Remove these items with the client before completing.</p>
                <ul>
                  {errors.map((error) => (
                    <li key={error}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>

        {receipt ? (
          <article className="label-panel" aria-live="polite">
            <p className="status-badge status-badge-approved status-bar">
              <Icon name="check" /> Checkout complete
            </p>
            <h2>Receipt #{receipt.checkout_id}</h2>
            <hr className="rule-heavy" />
            <div className="figure">
              <b>{receipt.total_lb}</b>
              <span>lb distributed</span>
            </div>
            <hr className="rule-mid" />
            <p className="why">Inventory was updated for every item in this cart.</p>
          </article>
        ) : (
          <div className="panel empty">
            <Icon name="checkout" />
            <strong>No receipt yet</strong>
            <span>Review the cart first. Restricted items stop checkout until they're removed.</span>
          </div>
        )}
      </div>
    </main>
  );
}
