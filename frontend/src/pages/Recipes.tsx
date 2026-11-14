import { useEffect, useState } from "react";

import { getRecipes, type Recipe } from "../api/client";

export default function Recipes() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [fallback, setFallback] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRecipes()
      .then((result) => {
        setRecipes(result.recipes);
        setFallback(result.used_fallback);
      })
      .catch(() => setRecipes([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">From your basket</span>
          <h1 className="page-title">
            Easy<br />recipes.
          </h1>
          <p className="page-subtitle">
            Smart, inventory-aware meal ideas crafted from your cart and current warehouse stock.
          </p>
        </div>
        <div className="choice-pill choice-pill-selected" style={{ width: "fit-content" }}>
          <span aria-hidden="true">✦</span>
          <span>Inventory-matched</span>
        </div>
      </div>

      {fallback && (
        <div
          style={{
            background: "var(--pastel-amber-bg)",
            border: "1px solid var(--pastel-amber-border)",
            color: "var(--pastel-amber-text)",
            padding: "0.85rem 1.25rem",
            borderRadius: "var(--radius-lg)",
            marginBottom: "1.5rem",
            fontSize: "0.9rem",
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
          }}
        >
          <span aria-hidden="true" style={{ fontSize: "1.2rem" }}>ℹ</span>
          <span>We used our rules-only recipe fallback while the recipe assistant was unavailable.</span>
        </div>
      )}

      {loading ? (
        <div className="ui-card" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
          <p style={{ margin: 0 }}>Matching recipes with your basket…</p>
        </div>
      ) : recipes.length === 0 ? (
        <div className="ui-card" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
          <span style={{ fontSize: "2.5rem", display: "block", marginBottom: "0.75rem", opacity: 0.5 }}>✦</span>
          <p style={{ margin: 0, fontWeight: 500 }}>No recipes available yet.</p>
          <p style={{ fontSize: "0.88rem", marginTop: "0.5rem" }}>
            Add items to your cart to generate custom recipe ideas.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem" }}>
          {recipes.map((recipe) => (
            <article key={recipe.title} className="ui-card ui-card-hover" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
                <h2 style={{ fontSize: "1.35rem", fontWeight: 700, margin: 0, color: "var(--text-dark)" }}>
                  {recipe.title}
                </h2>
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    padding: "0.25rem 0.65rem",
                    borderRadius: "var(--radius-pill)",
                    background: "var(--pastel-blue-bg)",
                    color: "var(--pastel-blue-text)",
                    border: "1px solid var(--pastel-blue-border)",
                    whiteSpace: "nowrap",
                  }}
                >
                  From your basket
                </span>
              </div>

              <div>
                <h3 style={{ fontSize: "0.9rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-muted)", margin: "0 0 0.5rem" }}>
                  Ingredients
                </h3>
                <ul style={{ margin: 0, paddingLeft: "1.25rem", color: "var(--text-body)", fontSize: "0.92rem", lineHeight: 1.6 }}>
                  {recipe.ingredients.map((ingredient) => (
                    <li key={ingredient.name}>{ingredient.name}</li>
                  ))}
                </ul>
              </div>

              <div style={{ borderTop: "1px solid var(--border-card)", paddingTop: "1rem" }}>
                <h3 style={{ fontSize: "0.9rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-muted)", margin: "0 0 0.5rem" }}>
                  Steps
                </h3>
                <ol style={{ margin: 0, paddingLeft: "1.25rem", color: "var(--text-body)", fontSize: "0.92rem", lineHeight: 1.6 }}>
                  {recipe.steps.map((step) => (
                    <li key={step} style={{ marginBottom: "0.35rem" }}>{step}</li>
                  ))}
                </ol>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
