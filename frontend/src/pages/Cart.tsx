import { useEffect, useState } from "react";

import { deleteCartItem, getCart, saveCartItem, type CartItem } from "../api/client";
import Icon from "../components/Icon";

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

      <section className="panel" aria-label="Cart items">
        {items.length === 0 ? (
          <div className="empty">
            <Icon name="cart" />
            <strong>Your cart is empty.</strong>
            <span>Add your picks from Home or scan a product to get started.</span>
          </div>
        ) : (
          <ul className="ingredients" style={{ margin: 0 }}>
            {items.map((item) => (
              <li key={item.product_id} style={{ alignItems: "center", padding: "0.75rem 0" }}>
                <div>
                  <h2 style={{ fontSize: "1.0625rem" }}>{item.name}</h2>
                  {item.from_recommendation && <span className="tag">Recommended for you</span>}
                </div>
                <div className="stepper">
                  <button
                    aria-label={`Decrease ${item.name}`}
                    type="button"
                    onClick={() => void update(item, item.quantity - 1)}
                  >
                    −
                  </button>
                  <output aria-live="polite">{item.quantity}</output>
                  <button
                    aria-label={`Increase ${item.name}`}
                    type="button"
                    onClick={() => void update(item, item.quantity + 1)}
                  >
                    +
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {items.length > 0 && (
        <a className="btn btn-secondary" href="/recipes" style={{ marginTop: "1rem" }}>
          <Icon name="recipes" /> Recipe ideas for this cart
        </a>
      )}
    </main>
  );
}
