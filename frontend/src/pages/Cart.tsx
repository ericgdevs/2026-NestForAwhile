import { useEffect, useState } from "react";

import { deleteCartItem, getCart, saveCartItem, type CartItem } from "../api/client";
import CheckoutQr from "../components/CheckoutQr";
import Icon from "../components/Icon";
import NotForLine from "../components/NotForLine";
import NutritionFacts from "../components/NutritionFacts";
import { StatusBadge } from "../components/StatusBadge";

// api/client-flow sends nutrition per item; until it merges, the panel shows once any value arrives.
const hasNutrition = (item: CartItem) =>
  [item.sodium_mg, item.sugar_g, item.sat_fat_g, item.potassium_mg].some((value) => value !== undefined);

export default function Cart() {
  const [items, setItems] = useState<CartItem[]>([]);
  const [showQr, setShowQr] = useState(false);

  async function refresh() {
    const cart = await getCart();
    setItems(cart.items);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function update(item: CartItem, quantity: number) {
    if (quantity < 1) {
      await deleteCartItem(item.product_id);
    } else {
      await saveCartItem(item.product_id, quantity);
    }
    await refresh();
  }

  const totalQuantity = items.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Your cart</h1>
          <p>Matches what's in your physical cart. A volunteer checks it at checkout.</p>
        </div>
        <div className="figure">
          <b>{totalQuantity}</b>
          <span>
            {totalQuantity === 1 ? "unit" : "units"} · {items.length} {items.length === 1 ? "item" : "items"}
          </span>
        </div>
      </header>

      {items.length === 0 ? (
        <div className="panel empty">
          <Icon name="cart" />
          <strong>Your cart is empty.</strong>
          <span>Add your picks from Home or scan a product to get started.</span>
        </div>
      ) : (
        <section aria-label="Cart items" className="grid grid-2">
          {items.map((item) => (
            <article key={item.product_id} className="label-panel">
              {item.status && <StatusBadge bar status={item.status} />}
              <NotForLine allergy={item.allergy_match} notFor={item.not_for} />
              <h2>{item.name}</h2>
              {item.sku && <p className="meta tabular">SKU {item.sku}</p>}
              <hr className="rule-heavy" />
              {hasNutrition(item) ? (
                <NutritionFacts facts={item} />
              ) : (
                <p className="why">Nutrition facts not available yet.</p>
              )}
              {item.explanation && (
                <p className="why">
                  <strong>Why: </strong>
                  {item.explanation}
                </p>
              )}
              <hr className="rule-heavy" />
              <div className="figure-row">
                <span>Quantity in cart:</span> <b>{item.quantity}</b>
              </div>
              <hr className="rule-mid" />
              {item.from_recommendation && (
                <span className="tag" style={{ alignSelf: "flex-start", marginBottom: "0.75rem" }}>
                  Recommended for you
                </span>
              )}
              <div className="stepper" style={{ marginTop: "auto", alignSelf: "stretch", justifyContent: "space-between" }}>
                <button aria-label={`Decrease ${item.name}`} type="button" onClick={() => void update(item, item.quantity - 1)}>
                  −
                </button>
                <output aria-live="polite">{item.quantity}</output>
                <button aria-label={`Increase ${item.name}`} type="button" onClick={() => void update(item, item.quantity + 1)}>
                  +
                </button>
              </div>
            </article>
          ))}
        </section>
      )}

      {items.length > 0 && (
        <section aria-label="Checkout" className="panel stack" style={{ marginTop: "1rem", maxWidth: "28rem" }}>
          <button
            aria-expanded={showQr}
            className="btn btn-primary"
            type="button"
            onClick={() => setShowQr((open) => !open)}
          >
            <Icon name="checkout" /> {showQr ? "Hide checkout code" : "Show at checkout"}
          </button>
          {showQr && (
            <>
              <p className="panel-sub">Show this to the volunteer at the exit desk.</p>
              <CheckoutQr />
            </>
          )}
        </section>
      )}

      {items.length > 0 && (
        <a className="btn btn-secondary" href="/recipes" style={{ marginTop: "1rem" }}>
          <Icon name="recipes" /> Recipe ideas for this cart
        </a>
      )}
    </main>
  );
}
