import { useState } from "react";

export default function Reports() {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function download(type: "donor" | "grant") {
    setError("");
    setDownloading(type);
    try {
      const response = await fetch(`/reports/${type}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      if (!response.ok) throw new Error("Report generation failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${type}-report.docx`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setError(`Failed to download ${type} report. Please try again.`);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Funding &amp; Compliance</span>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">
            Export structured DOCX documents containing donor attribution, food totals, and visit metrics.
          </p>
        </div>
      </div>

      <section className="ui-card" style={{ maxWidth: "680px", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
        <div>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 0.35rem" }}>Export reports</h2>
          <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--text-muted)" }}>
            Select a report format below. The system populates data from verified checkout logs.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}>
          <div className="stat-tile stat-tile-blue" style={{ justifyContent: "space-between", gap: "1rem" }}>
            <div>
              <span className="stat-label">Donor attribution</span>
              <p style={{ margin: "0.35rem 0 0", fontSize: "0.9rem", color: "var(--text-body)" }}>
                Aggregated donor volume, pounds distributed, and synthetic partner impact.
              </p>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => download("donor")}
              disabled={downloading !== null}
            >
              {downloading === "donor" ? "Generating…" : "Download donor report"}
            </button>
          </div>

          <div className="stat-tile stat-tile-green" style={{ justifyContent: "space-between", gap: "1rem" }}>
            <div>
              <span className="stat-label">Grant metrics</span>
              <p style={{ margin: "0.35rem 0 0", fontSize: "0.9rem", color: "var(--text-body)" }}>
                Four-section grant documentation with visit counts and inventory allocations.
              </p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => download("grant")}
              disabled={downloading !== null}
            >
              {downloading === "grant" ? "Generating…" : "Download grant report"}
            </button>
          </div>
        </div>

        {error && (
          <p
            style={{
              margin: 0,
              fontSize: "0.88rem",
              color: "var(--pastel-rose-text)",
              background: "var(--pastel-rose-bg)",
              border: "1px solid var(--pastel-rose-border)",
              padding: "0.75rem 1rem",
              borderRadius: "var(--radius-md)",
            }}
          >
            {error}
          </p>
        )}
      </section>
    </main>
  );
}
