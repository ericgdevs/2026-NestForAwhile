import { useEffect, useState } from "react";
import { getReplenishment } from "../api/client";

export default function Replenishment() {
  const [items, setItems] = useState<Awaited<ReturnType<typeof getReplenishment>>>([]);
  const [sort, setSort] = useState("priority");

  useEffect(() => {
    getReplenishment(sort).then(setItems).catch(() => setItems([]));
  }, [sort]);

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Floor restocking</span>
          <h1 className="page-title">Replenishment</h1>
          <p className="page-subtitle">
            Items below safety threshold. Restock directly from warehouse storage locations.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span className="stat-label">Sort by:</span>
          <select
            className="form-input"
            style={{ width: "auto", padding: "0.45rem 1rem", fontSize: "0.88rem" }}
            value={sort}
            onChange={(event) => setSort(event.target.value)}
          >
            <option value="priority">Priority</option>
            <option value="location">Location</option>
            <option value="name">Name</option>
          </select>
        </div>
      </div>

      <section className="ui-card">
        <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          {items.length === 0 ? (
            <p style={{ margin: 0, color: "var(--text-muted)" }}>All warehouse inventory items are currently above threshold.</p>
          ) : (
            items.map((item) => (
              <article
                key={`${item.product_id}-${item.aisle}-${item.bin}`}
                className="item-card ui-card-hover"
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "1rem 1.25rem",
                }}
              >
                <div>
                  <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 0.25rem", color: "var(--text-dark)" }}>
                    {item.name}
                  </h2>
                  <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    Stock level: <strong>{item.quantity}</strong> / {item.reorder_threshold} units
                  </p>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span
                    style={{
                      fontSize: "0.82rem",
                      fontWeight: 600,
                      padding: "0.3rem 0.75rem",
                      borderRadius: "var(--radius-pill)",
                      background: "var(--pastel-blue-bg)",
                      color: "var(--pastel-blue-text)",
                      border: "1px solid var(--pastel-blue-border)",
                    }}
                  >
                    Aisle {item.aisle} • Shelf {item.shelf} • Bin {item.bin}
                  </span>
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
