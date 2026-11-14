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

  return (
    <main className="space-y-6">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-stone-500">Ready when you are</p>
        <h1 aria-label="Your cart" className="display-title mt-3">Your cart,<br />beautifully simple.</h1>
      </div>
        {items.length === 0 && <p className="soft-card p-5 text-stone-500">Your cart is empty.</p>}
        {items.map((item) => (
          <article key={item.product_id} className="soft-card flex items-center justify-between p-4">
            <div>
              <h2 className="font-semibold">{item.name}</h2>
              {item.from_recommendation && <p className="text-sm text-[#d66d43]">Recommended for you</p>}
            </div>
            <div className="flex items-center gap-2">
              <button aria-label={`Decrease ${item.name}`} onClick={() => void update(item, item.quantity - 1)}>-</button>
              <span>{item.quantity}</span>
              <button aria-label={`Increase ${item.name}`} onClick={() => void update(item, item.quantity + 1)}>+</button>
            </div>
          </article>
        ))}
    </main>
  );
}
