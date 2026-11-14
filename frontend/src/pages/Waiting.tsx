import { useEffect, useState } from "react";
import { claimQueue, getQueue } from "../api/client";

export default function Waiting() {
  const [queue, setQueue] = useState<{ status: string; position: number | null; message: string } | null>(null);

  useEffect(() => {
    getQueue().then(setQueue).catch(() => setQueue(null));
  }, []);

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Floor access</span>
          <h1 className="page-title">Queue</h1>
          <p className="page-subtitle">
            Live waiting room and capacity status. You will be invited in as shoppers finish.
          </p>
        </div>
      </div>

      <section className="ui-card" style={{ maxWidth: "540px", textAlign: "center", padding: "2.5rem 2rem" }}>
        {queue ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1.25rem" }}>
            <span
              style={{
                width: "4rem",
                height: "4rem",
                borderRadius: "50%",
                background: queue.status === "ready" ? "var(--pastel-green-bg)" : "var(--pastel-blue-bg)",
                color: queue.status === "ready" ? "var(--pastel-green-text)" : "var(--pastel-blue-text)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.75rem",
              }}
            >
              {queue.status === "ready" ? "✓" : "◷"}
            </span>

            <p style={{ fontSize: "1.15rem", fontWeight: 600, margin: 0, color: "var(--text-dark)" }}>
              {queue.message}
            </p>

            {queue.position && (
              <div className="stat-tile stat-tile-blue" style={{ width: "100%", textAlign: "center", margin: "0.5rem 0" }}>
                <span className="stat-label">Your spot in line</span>
                <p className="stat-number" style={{ fontSize: "2.75rem" }}>Position: {queue.position}</p>
                <p className="stat-caption">We will notify you immediately when a floor spot opens.</p>
              </div>
            )}

            {queue.status === "ready" && (
              <button
                className="btn btn-accent"
                style={{ width: "100%", padding: "0.85rem", fontSize: "1.05rem" }}
                onClick={() => claimQueue()}
              >
                Come in
              </button>
            )}
          </div>
        ) : (
          <p style={{ margin: 0, color: "var(--text-muted)" }}>Checking current queue status…</p>
        )}
      </section>
    </main>
  );
}
