import { useEffect, useState } from "react";

import { getAnalytics } from "../api/client";

type Metrics = Awaited<ReturnType<typeof getAnalytics>>;

function display(key: string, value: number) {
  return key.includes("rate") ? `${(value * 100).toFixed(0)}%` : value.toLocaleString();
}

export default function Analytics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    getAnalytics().then(setMetrics).catch(() => setMetrics(null));
  }, []);

  const totals = metrics
    ? (Object.entries(metrics).filter(([key]) => key !== "waste_reduction") as [string, number][])
    : [];

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Analytics</h1>
          <p>Anonymized totals to date. No personal details are shown or exported.</p>
        </div>
        {metrics && (
          <div className="figure">
            <b>{metrics.families_served.toLocaleString()}</b>
            <span>{metrics.families_served === 1 ? "family" : "families"} served to date</span>
          </div>
        )}
      </header>

      {metrics ? (
        <section className="label-panel" style={{ maxWidth: "40rem" }}>
          <h2 className="panel-title">Totals to date</h2>
          <dl className="facts">
            {totals.map(([key, value]) => (
              <div key={key}>
                <dt className="metric-name">{key.replaceAll("_", " ")}</dt>
                <dd>{display(key, value)}</dd>
              </div>
            ))}
          </dl>
          <h3 className="facts subhead">Waste reduction</h3>
          <dl className="facts">
            <div>
              <dt>Pounds saved from near-expiry lots</dt>
              <dd>{metrics.waste_reduction.pounds_saved} lb</dd>
            </div>
            <div>
              <dt>Lots expiring within seven days</dt>
              <dd>{metrics.waste_reduction.expiring_soon_lots}</dd>
            </div>
          </dl>
        </section>
      ) : (
        <p className="empty">Loading totals…</p>
      )}
    </main>
  );
}
