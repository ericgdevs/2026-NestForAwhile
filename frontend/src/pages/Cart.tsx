import { useEffect, useState } from "react";

import { deleteCartItem, getCart, saveCartItem, type CartItem } from "../api/client";

export default function Cart() {
  const [items, setItems] = useState<CartItem[]>([]);

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
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Ready when you are</span>
          <h1 aria-label="Your cart" className="page-title">
            Your cart,<br />beautifully simple.
          </h1>
          <p className="page-subtitle">
            Review items in your active shopping session before checkout.
          </p>
        </div>
        <div className="choice-pill choice-pill-selected" style={{ width: "fit-content" }}>
          <span>{items.length} {items.length === 1 ? "item" : "items"} ({totalQuantity} total units)</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1.5rem" }}>
        <section className="ui-card">
          {items.length === 0 ? (
            <div style={{ padding: "3rem 1rem", textAlign: "center", color: "var(--text-muted)" }}>
              <span style={{ fontSize: "2.5rem", display: "block", marginBottom: "0.75rem", opacity: 0.5 }}>🛒</span>
              <p style={{ margin: 0, fontWeight: 500 }}>Your cart is empty.</p>
              <p style={{ fontSize: "0.88rem", marginTop: "0.5rem" }}>
                Add recommended products or scan barcodes to get started.
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {items.map((item) => (
                <article
                  key={item.product_id}
                  className="item-card ui-card-hover"
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "1.25rem 1.5rem",
                  }}
                >
                  <div>
                    <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: "0 0 0.35rem", color: "var(--text-dark)" }}>
                      {item.name}
                    </h2>
                    {item.from_recommendation && (
                      <span
                        style={{
                          display: "inline-block",
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          padding: "0.2rem 0.65rem",
                          borderRadius: "var(--radius-pill)",
                          background: "var(--pastel-purple-bg)",
                          color: "var(--pastel-purple-text)",
                          border: "1px solid var(--pastel-purple-border)",
                        }}
                      >
                        Recommended for you
                      </span>
                    )}
                  </div>

                  <div className="quantity-controls">
                    <button
                      className="quantity-btn"
                      aria-label={`Decrease ${item.name}`}
                      onClick={() => void update(item, item.quantity - 1)}
                    >
                      -
                    </button>
                    <span style={{ minWidth: "1.5rem", textAlign: "center", fontWeight: 700, fontSize: "0.95rem" }}>
                      {item.quantity}
                    </span>
                    <button
                      className="quantity-btn"
                      aria-label={`Increase ${item.name}`}
                      onClick={() => void update(item, item.quantity + 1)}
                    >
                      +
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
