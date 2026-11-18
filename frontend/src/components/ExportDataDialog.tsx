import { useEffect, useRef, useState } from "react";

import { downloadReportData, type ReportFilters } from "../api/client";
import Icon from "./Icon";

const FORMATS = [
  { value: "csv", label: "CSV", hint: "Opens in Excel or Google Sheets" },
  { value: "json", label: "JSON", hint: "For other software and analysis" },
] as const;

/** Pick CSV or JSON, then download every row that matches the current filters. */
export default function ExportDataDialog({ filters, onClose }: { filters: ReportFilters; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [format, setFormat] = useState<"csv" | "json">("csv");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    dialog.current?.showModal();
  }, []);

  async function save() {
    setBusy(true);
    setError("");
    try {
      await downloadReportData(format, filters);
      onClose();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "We couldn't export the data. Try again.");
      setBusy(false);
    }
  }

  return (
    <dialog aria-labelledby="export-data-title" className="dialog" ref={dialog} onClose={onClose}>
      <form
        className="stack"
        method="dialog"
        onSubmit={(event) => {
          event.preventDefault();
          void save();
        }}
      >
        <h2 id="export-data-title">Export data</h2>
        <p className="panel-sub">Every visit that matches the filters on this page, as anonymous rows.</p>
        <fieldset className="choice-group" disabled={busy}>
          <legend className="field-label">File type</legend>
          {FORMATS.map((option) => (
            <label className="choice" key={option.value}>
              <input checked={format === option.value} name="export-format" type="radio" onChange={() => setFormat(option.value)} />
              <span>
                <strong>{option.label}</strong> <span className="panel-sub">{option.hint}</span>
              </span>
            </label>
          ))}
        </fieldset>
        {error && (
          <p className="alert alert-danger" role="alert">
            <Icon name="alert" />
            {error}
          </p>
        )}
        <div className="row report-actions">
          <button className="btn btn-primary" disabled={busy} type="submit">
            <Icon name="restock" /> Export
          </button>
          <button className="btn btn-secondary" type="button" onClick={() => dialog.current?.close()}>
            Cancel
          </button>
        </div>
      </form>
    </dialog>
  );
}
