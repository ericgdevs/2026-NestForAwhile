import { useEffect, useState } from "react";

import { getRecommendations, saveCartItem, type Recommendation } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export default function Home() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  useEffect(() => {
    getRecommendations().then(setRecommendations).catch(() => setRecommendations([]));
  }, []);

  return (
    <main className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-stone-500">Good to see you</p>
          <h1 className="display-title mt-3">MTG Warehouse<br />shop smarter.</h1>
        </div>
        <span className="pill text-xs font-bold text-stone-600"><span className="status-dot" aria-hidden="true" />AI matched</span>
      </div>
      <section className="soft-card overflow-hidden bg-[#20364c] p-5 text-stone-50 sm:p-6" aria-labelledby="recommendations-heading">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#a9d5fa]">Your next best picks</p>
            <h2 id="recommendations-heading" className="mt-3 text-2xl font-semibold tracking-tight">
              Food that fits your needs.
            </h2>
          </div>
          <span className="text-3xl" aria-hidden="true">✦</span>
        </div>
        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {recommendations.length === 0 && (
            <p className="rounded-2xl bg-white/10 p-4 text-stone-300">No recommendations yet.</p>
          )}
          {recommendations.map((item) => (
            <article key={item.product_id} className="rounded-[1.25rem] bg-[#edf5fc] p-4 text-stone-900 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-semibold">{item.name}</h3>
                <StatusBadge status={item.status} />
              </div>
              <p className="mt-3 text-sm text-stone-500">{item.rationale}</p>
              <p className="mt-4 text-sm">
                Suggested quantity: <strong>{item.quantity}</strong>
              </p>
              <button
                className="accent-button mt-4 px-4 py-2 text-sm"
                onClick={() => void saveCartItem(item.product_id, item.quantity)}
              >
                Add to cart
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
