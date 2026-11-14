import { useEffect, useState } from "react";
import { getInventoryLots } from "../api/client";

export default function Lots() {
  const [lots, setLots] = useState<Awaited<ReturnType<typeof getInventoryLots>>>([]);
  useEffect(() => {
    getInventoryLots().then(setLots).catch(() => setLots([]));
  }, []);

  const expiring = lots.some((lot) => lot.expiring_soon);

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Inventory tracking</span>
          <h1 className="page-title">FIFO lots</h1>
          <p className="page-subtitle">
            Track lot batches in FIFO rotation to reduce waste and ensure timely distribution.
          </p>
        </div>
      </div>

      {expiring && (
        <div
          role="alert"
          style={{
            background: "var(--pastel-amber-bg)",
            border: "1px solid var(--pastel-amber-border)",
            color: "var(--pastel-amber-text)",
            padding: "0.85rem 1.25rem",
            borderRadius: "var(--radius-lg)",
            marginBottom: "1.5rem",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "0.6rem",
          }}
        >
          <span aria-hidden="true">⚠</span>
          <span>Some lots expire within seven days.</span>
        </div>
      )}

      <section className="ui-card">
        <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
          {lots.length === 0 ? (
            <p style={{ margin: 0, color: "var(--text-muted)" }}>No inventory lots recorded.</p>
          ) : (
            lots.map((lot) => (
              <article
                key={lot.lot_id}
                className="item-card ui-card-hover"
                style={{
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "1rem 1.25rem",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                  <span
                    style={{
                      fontWeight: 700,
                      color: "var(--text-dark)",
                      fontSize: "0.95rem",
                      background: "#f1f5f9",
                      padding: "0.3rem 0.65rem",
                      borderRadius: "var(--radius-sm)",
                    }}
                  >
                    Lot #{lot.lot_id}
                  </span>
                  <div>
                    <p style={{ margin: 0, fontWeight: 600, fontSize: "0.95rem" }}>
                      Product #{lot.product_id}
                    </p>
                    <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-muted)" }}>
                      Expires: {lot.expiration_date}
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <span style={{ fontWeight: 700, fontSize: "1.05rem", color: "var(--text-dark)" }}>
                    {lot.quantity} units
                  </span>
                  {lot.expiring_soon && (
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        padding: "0.25rem 0.65rem",
                        borderRadius: "var(--radius-pill)",
                        background: "var(--pastel-amber-bg)",
                        color: "var(--pastel-amber-text)",
                        border: "1px solid var(--pastel-amber-border)",
                      }}
                    >
                      Expiring soon
                    </span>
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
