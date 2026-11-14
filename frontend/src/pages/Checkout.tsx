import { FormEvent, useState } from "react";

import {
  acknowledgeAllergy,
  addCheckoutItem,
  completeCheckout,
  lookupCheckout,
  overrideItem,
  removeCheckoutItem,
  type CheckoutReview,
} from "../api/client";
import BarcodeScanner from "../components/BarcodeScanner";
import Icon from "../components/Icon";
import NotForLine from "../components/NotForLine";
import { StatusBadge } from "../components/StatusBadge";
import { useAuth } from "../lib/auth";

export default function Checkout() {
  const { user } = useAuth();
  const isManager = user?.role === "Warehouse Manager";
  const [clientId, setClientId] = useState("");
  const [itemCode, setItemCode] = useState("");
  const [review, setReview] = useState<CheckoutReview | null>(null);
  const [receipt, setReceipt] = useState<{ checkout_id: number; total_lb: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState("");

  // Every action returns the fresh review, so the screen always shows the server's view.
  async function run(action: () => Promise<CheckoutReview | void>) {
    setLoading(true);
    setRequestError("");
    try {
      const next = await action();
      if (next) setReview(next);
    } catch (reason) {
      setRequestError(reason instanceof Error ? reason.message : "That didn't work. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function findClient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const id = Number(clientId);
    if (Number.isInteger(id) && id > 0) void run(() => lookupCheckout({ client_id: id }));
  }

  function addItem(code: string) {
    if (review && code.trim()) {
      void run(() => addCheckoutItem(review.Shopping_Session_Token, code.trim()));
      setItemCode("");
    }
  }

  function override(productId: number) {
    const note = window.prompt("Why is this item being let through? (logged)");
    if (review && note?.trim()) void run(() => overrideItem(review.Shopping_Session_Token, productId, note.trim()));
  }

  function complete() {
    if (!review) return;
    void run(async () => {
      setReceipt(await completeCheckout(review.Shopping_Session_Token));
    });
  }

  function startOver() {
    setReview(null);
    setReceipt(null);
    setClientId("");
  }

  const ackIds = new Set(review?.needs_ack.map((entry) => entry.product_id));
  const ready = review !== null && review.blocking.length === 0 && review.needs_ack.length === 0;

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Checkout</h1>
          <p>Scan the QR code on the client's phone, check their cart against the physical cart, then complete the visit.</p>
        </div>
        {review && !receipt && (
          <div className="figure">
            <b>{review.items.reduce((sum, item) => sum + item.quantity, 0)}</b>
            <span>units for client #{review.client_id}</span>
          </div>
        )}
      </header>

      {requestError && (
        <p className="alert alert-danger" role="alert" style={{ marginBottom: "1rem" }}>
          <Icon name="alert" />
          {requestError}. Check with the client and try again.
        </p>
      )}

      {receipt ? (
        <article className="label-panel" aria-live="polite" style={{ maxWidth: "32rem" }}>
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
          <button className="btn btn-primary" style={{ marginTop: "1rem" }} type="button" onClick={startOver}>
            Next client
          </button>
        </article>
      ) : !review ? (
        <section className="panel stack" aria-label="Find the client" style={{ maxWidth: "32rem" }}>
          <h2>Find the client</h2>
          <BarcodeScanner onDetected={(token) => void run(() => lookupCheckout({ token }))} />
          <p className="divider-text">or type their client ID</p>
          <form className="field" onSubmit={findClient}>
            <label className="field-label" htmlFor="client-id">
              Client ID
            </label>
            <div className="inline-form">
              <input
                className="input tabular"
                id="client-id"
                inputMode="numeric"
                placeholder="Shown on the client's cart screen"
                value={clientId}
                onChange={(event) => setClientId(event.target.value)}
              />
              <button className="btn btn-primary" disabled={loading || !clientId.trim()} type="submit">
                Load cart
              </button>
            </div>
          </form>
        </section>
      ) : (
        <div className="grid grid-2" style={{ alignItems: "start" }}>
          <section className="panel stack" aria-label="Cart to confirm">
            <h2>Confirm against the physical cart</h2>
            <ul className="list-lines">
              {review.items.map((item) => (
                <li className="list-line" key={item.product_id}>
                  <div className="row">
                    <strong>
                      {item.quantity} × {item.name}
                    </strong>
                    <StatusBadge status={item.status} />
                  </div>
                  <NotForLine allergy={item.allergy_match} notFor={item.not_for} />
                  <div className="row" style={{ justifyContent: "flex-start", flexWrap: "wrap" }}>
                    {ackIds.has(item.product_id) && (
                      <button
                        className="btn btn-primary"
                        disabled={loading}
                        type="button"
                        onClick={() => void run(() => acknowledgeAllergy(review.Shopping_Session_Token, item.product_id))}
                      >
                        Confirmed with client
                      </button>
                    )}
                    {item.acknowledged && <span className="tag">Allergy confirmed</span>}
                    {item.status === "Restricted" && !item.overridden && isManager && (
                      <button className="btn btn-secondary" disabled={loading} type="button" onClick={() => override(item.product_id)}>
                        Manager override
                      </button>
                    )}
                    {item.overridden && <span className="tag">Manager override</span>}
                    <button
                      aria-label={`Remove ${item.name}`}
                      className="btn btn-secondary"
                      disabled={loading}
                      type="button"
                      onClick={() => void run(() => removeCheckoutItem(review.Shopping_Session_Token, item.product_id))}
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            <form
              className="field"
              onSubmit={(event) => {
                event.preventDefault();
                addItem(itemCode);
              }}
            >
              <label className="field-label" htmlFor="missed-item">
                Missed an item? Scan or type its barcode
              </label>
              <div className="inline-form">
                <input
                  className="input"
                  id="missed-item"
                  placeholder="SKU or barcode"
                  value={itemCode}
                  onChange={(event) => setItemCode(event.target.value)}
                />
                <button className="btn btn-secondary" disabled={loading || !itemCode.trim()} type="submit">
                  Add item
                </button>
              </div>
            </form>
            <BarcodeScanner onDetected={addItem} />
          </section>

          <section className="panel stack" aria-label="Before you finish">
            <h2>Before you finish</h2>
            {review.blocking.length === 0 && review.needs_ack.length === 0 ? (
              <p className="alert alert-ok" role="status">
                <Icon name="check" />
                Everything checks out.
              </p>
            ) : (
              <div className="alert alert-danger" role="alert">
                <Icon name="stop" />
                <div>
                  <strong>Checkout needs attention</strong>
                  <ul>
                    {review.blocking.map((stop) => (
                      <li key={stop}>{stop}</li>
                    ))}
                    {review.needs_ack.map((entry) => (
                      <li key={entry.product_id}>
                        Confirm with the client: {entry.name} is not for{" "}
                        {entry.not_for.map((who) => `${who.nickname} (${who.reason})`).join(", ")}.
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            <button className="btn btn-primary btn-block" disabled={loading || !ready} type="button" onClick={complete}>
              Complete checkout
            </button>
            <button className="btn btn-secondary" type="button" onClick={startOver}>
              Different client
            </button>
          </section>
        </div>
      )}
    </main>
  );
}
