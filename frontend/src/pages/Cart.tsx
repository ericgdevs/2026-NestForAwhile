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
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-2xl font-semibold">Your cart</h1>
        {items.length === 0 && <p className="rounded-lg bg-white p-4">Your cart is empty.</p>}
        {items.map((item) => (
          <article key={item.product_id} className="flex items-center justify-between rounded-xl bg-white p-4 shadow-sm">
            <div>
              <h2 className="font-semibold">{item.name}</h2>
              {item.from_recommendation && <p className="text-sm text-emerald-800">Recommended for you</p>}
            </div>
            <div className="flex items-center gap-2">
              <button aria-label={`Decrease ${item.name}`} onClick={() => void update(item, item.quantity - 1)}>-</button>
              <span>{item.quantity}</span>
              <button aria-label={`Increase ${item.name}`} onClick={() => void update(item, item.quantity + 1)}>+</button>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
