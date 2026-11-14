import { useEffect, useState } from "react";

import { getRecommendations, saveCartItem, type Recommendation } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export default function Home() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [addedIds, setAddedIds] = useState<number[]>([]);

  useEffect(() => {
    getRecommendations().then(setRecommendations).catch(() => setRecommendations([]));
  }, []);

  async function handleAdd(item: Recommendation) {
    await saveCartItem(item.product_id, item.quantity);
    setAddedIds((prev) => [...prev, item.product_id]);
    setTimeout(() => {
      setAddedIds((prev) => prev.filter((id) => id !== item.product_id));
    }, 2000);
  }

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Good to see you</span>
          <h1 className="page-title">
            MTG Warehouse<br />shop smarter.
          </h1>
          <p className="page-subtitle">
            Personalized, dietary-safe grocery picks tailored to your profile and household size.
          </p>
        </div>
        <div className="choice-pill choice-pill-selected" style={{ width: "fit-content" }}>
          <span aria-hidden="true">✦</span>
          <span>AI matched</span>
        </div>
      </div>

      <section aria-labelledby="recommendations-heading" className="ui-card" style={{ padding: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
          <div>
            <span className="stat-label">Your next best picks</span>
            <h2 id="recommendations-heading" style={{ fontSize: "1.45rem", fontWeight: 700, margin: "0.25rem 0 0" }}>
              Food that fits your needs.
            </h2>
          </div>
          <span
            aria-hidden="true"
            style={{
              width: "2.5rem",
              height: "2.5rem",
              borderRadius: "50%",
              background: "var(--pastel-blue-bg)",
              color: "var(--pastel-blue-text)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.1rem",
            }}
          >
            ✦
          </span>
        </div>

        {recommendations.length === 0 ? (
          <div style={{ padding: "3rem 1rem", textAlign: "center", color: "var(--text-muted)" }}>
            <p style={{ margin: 0 }}>No recommendations yet.</p>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1.25rem",
            }}
          >
            {recommendations.map((item) => {
              const isAdded = addedIds.includes(item.product_id);
              return (
                <article key={item.product_id} className="item-card ui-card-hover">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
                    <h3 style={{ fontSize: "1.15rem", fontWeight: 700, margin: 0, color: "var(--text-dark)" }}>
                      {item.name}
                    </h3>
                    <StatusBadge status={item.status} />
                  </div>

                  <p style={{ color: "var(--text-body)", fontSize: "0.9rem", lineHeight: 1.5, margin: 0 }}>
                    {item.rationale}
                  </p>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginTop: "auto",
                      paddingTop: "0.85rem",
                      borderTop: "1px solid var(--border-card)",
                    }}
                  >
                    <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--text-muted)" }}>
                      Suggested quantity: <strong>{item.quantity}</strong>
                    </p>
                    {item.aisle && (
                      <span
                        style={{
                          fontSize: "0.75rem",
                          fontWeight: 600,
                          padding: "0.2rem 0.55rem",
                          borderRadius: "var(--radius-pill)",
                          background: "#f1f5f9",
                          color: "var(--text-body)",
                        }}
                      >
                        Aisle {item.aisle}
                      </span>
                    )}
                  </div>

                  <button
                    className={`btn ${isAdded ? "btn-secondary" : "btn-primary"}`}
                    style={{ width: "100%", marginTop: "0.5rem" }}
                    onClick={() => void handleAdd(item)}
                  >
                    {isAdded ? "Added to cart ✓" : "Add to cart"}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
