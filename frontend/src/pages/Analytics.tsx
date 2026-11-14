import { useEffect, useState } from "react";
import { getAnalytics } from "../api/client";

export default function Analytics() {
  const [metrics, setMetrics] = useState<Awaited<ReturnType<typeof getAnalytics>> | null>(null);

  useEffect(() => {
    getAnalytics().then(setMetrics).catch(() => setMetrics(null));
  }, []);

  const tileClasses = [
    "stat-tile stat-tile-purple",
    "stat-tile stat-tile-blue",
    "stat-tile stat-tile-green",
    "stat-tile stat-tile-amber",
    "stat-tile",
  ];

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Operations intelligence</span>
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">
            Anonymized distribution totals, family impact, and inventory utilization.
          </p>
        </div>
      </div>

      {metrics && (
        <>
          <dl className="stat-grid">
            {Object.entries(metrics)
              .filter(([key]) => key !== "waste_reduction")
              .map(([key, value], idx) => {
                const tileClass = tileClasses[idx % tileClasses.length];
                const displayValue =
                  typeof value === "number" && key.includes("rate")
                    ? `${(value * 100).toFixed(0)}%`
                    : String(value);

                return (
                  <div key={key} className={tileClass}>
                    <dt className="stat-label">{key.replaceAll("_", " ")}</dt>
                    <dd className="stat-number">{displayValue}</dd>
                    <p className="stat-caption">Total recorded to date</p>
                  </div>
                );
              })}
          </dl>

          {metrics.waste_reduction && (
            <section className="ui-card" style={{ marginTop: "1rem" }}>
              <span className="stat-label">Waste reduction impact</span>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0.25rem 0 1rem" }}>
                Preserved inventory
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }}>
                <div className="stat-tile stat-tile-green" style={{ boxShadow: "none" }}>
                  <span className="stat-label">Pounds saved</span>
                  <p className="stat-number">{metrics.waste_reduction.pounds_saved} lb</p>
                  <p className="stat-caption">rescued from near-expiration</p>
                </div>
                <div className="stat-tile stat-tile-amber" style={{ boxShadow: "none" }}>
                  <span className="stat-label">Expiring lots monitored</span>
                  <p className="stat-number">{metrics.waste_reduction.expiring_soon_lots}</p>
                  <p className="stat-caption">active priority batches</p>
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}
