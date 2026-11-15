import { useEffect, useState } from "react";

import { getAnalytics } from "../api/client";
import StatGrid, { type Stat } from "../components/StatGrid";

type Metrics = Awaited<ReturnType<typeof getAnalytics>>;

function totalsFor(metrics: Metrics): Stat[] {
  return [
    { label: "Families served", value: metrics.families_served, icon: "home", tone: "blue" },
    { label: "Visits completed", value: metrics.visits_completed, icon: "checkout", tone: "ok" },
    { label: "Pounds distributed", value: metrics.pounds_distributed, icon: "cart", tone: "blue" },
    { label: "Units given out", value: metrics.inventory_usage, icon: "lots", tone: "ok" },
    { label: "Picks taken from recommendations", value: `${Math.round(metrics.recommendation_adoption_rate * 100)}%`, icon: "check", tone: "blue" },
  ];
}

function wasteFor(metrics: Metrics): Stat[] {
  return [
    { label: "Pounds saved from near-expiry lots", value: metrics.waste_reduction.pounds_saved, icon: "restock", tone: "ok" },
    { label: "Lots expiring within 7 days", value: metrics.waste_reduction.expiring_soon_lots, icon: "alert", tone: "warn" },
  ];
}

export default function Analytics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    getAnalytics().then(setMetrics).catch(() => setMetrics(null));
  }, []);

  return (
    <main>
      <header className="page-head page-head-plain">
        <div>
          <h1>Analytics</h1>
          <p>Anonymized totals to date. No personal details are shown or exported.</p>
        </div>
      </header>

      {metrics ? (
        <>
          <section aria-label="Totals to date">
            <h2 className="panel-title" style={{ marginBottom: "1rem" }}>
              Totals to date
            </h2>
            <StatGrid stats={totalsFor(metrics)} />
          </section>
          <section aria-label="Waste reduction" style={{ marginTop: "2rem" }}>
            <h2 className="panel-title" style={{ marginBottom: "1rem" }}>
              Waste reduction
            </h2>
            <StatGrid stats={wasteFor(metrics)} />
          </section>
        </>
      ) : (
        <p className="empty">Loading totals…</p>
      )}
    </main>
  );
}
