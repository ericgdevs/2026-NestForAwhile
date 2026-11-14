import { useEffect, useState } from "react";

import { getRecommendations, saveCartItem, type Recommendation } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export default function Home() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  useEffect(() => {
    getRecommendations().then(setRecommendations).catch(() => setRecommendations([]));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold">NestForAwhile MTG Warehouse</h1>
        <p className="mt-2 text-slate-600">Grocery matches for your household.</p>
        <section className="mt-6 space-y-3" aria-labelledby="recommendations-heading">
          <h2 id="recommendations-heading" className="text-lg font-semibold">
            Recommended for you
          </h2>
          {recommendations.length === 0 && (
            <p className="rounded-lg bg-white p-4 text-slate-600">No recommendations yet.</p>
          )}
          {recommendations.map((item) => (
            <article key={item.product_id} className="rounded-xl bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h3 className="font-semibold">{item.name}</h3>
                <StatusBadge status={item.status} />
              </div>
              <p className="mt-2 text-sm text-slate-600">{item.rationale}</p>
              <p className="mt-2 text-sm">
                Suggested quantity: <strong>{item.quantity}</strong>
              </p>
              <button
                className="mt-3 rounded-lg border px-3 py-2 text-sm"
                onClick={() => void saveCartItem(item.product_id, item.quantity)}
              >
                Add to cart
              </button>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
