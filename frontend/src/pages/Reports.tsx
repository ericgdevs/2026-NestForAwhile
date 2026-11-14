import { useState } from "react";

import Icon from "../components/Icon";

const reports = [
  {
    type: "donor",
    title: "Donor report",
    body: "Donor metrics, pounds distributed, and visit totals.",
  },
  {
    type: "grant",
    title: "Grant report",
    body: "Grant attribution, food distribution totals, and visit metrics.",
  },
] as const;

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
      <header className="page-head">
        <div>
          <h1>Reports</h1>
          <p>Download a Word (DOCX) report built from anonymized checkout records.</p>
        </div>
      </header>

      <div className="grid grid-2">
        {reports.map((report) => (
          <article className="label-panel" key={report.type}>
            <h2>{report.title}</h2>
            <hr className="rule-heavy" />
            <p className="why" style={{ marginBottom: "1rem" }}>
              {report.body}
            </p>
            <button
              className="btn btn-primary btn-block"
              disabled={downloading !== null}
              style={{ marginTop: "auto" }}
              type="button"
              onClick={() => void download(report.type)}
            >
              <Icon name="reports" />
              {downloading === report.type ? "Generating…" : `Download ${report.type} report`}
            </button>
          </article>
        ))}
      </div>

      {error && (
        <p className="alert alert-danger" role="alert" style={{ marginTop: "1rem" }}>
          <Icon name="alert" />
          {error}
        </p>
      )}
    </main>
  );
}
