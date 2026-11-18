import { useEffect, useRef, useState } from "react";

import { downloadWrittenReport, type ReportAudience, type ReportFilters, type ReportFormat } from "../api/client";
import Icon from "./Icon";

const AUDIENCES: { value: ReportAudience; label: string; hint: string }[] = [
  { value: "donor", label: "Donor", hint: "Thanks and impact for donors" },
  { value: "grant", label: "Grant funder", hint: "Outcomes for a grant report" },
  { value: "general", label: "General", hint: "Board and community summary" },
];
const FORMATS: { value: ReportFormat; label: string }[] = [
  { value: "pdf", label: "PDF" },
  { value: "docx", label: "Word document" },
  { value: "both", label: "Both (one ZIP file)" },
];

/** Pick who the report is for and which file(s) to get, then download it with the current filters. */
export default function WrittenReportDialog({ filters, onClose }: { filters: ReportFilters; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [audience, setAudience] = useState<ReportAudience>("donor");
  const [format, setFormat] = useState<ReportFormat>("docx");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    dialog.current?.showModal();
  }, []);

  async function generate() {
    setBusy(true);
    setError("");
    try {
      await downloadWrittenReport(audience, format, filters);
      onClose();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "We couldn't create the report. Try again.");
      setBusy(false);
    }
  }

  return (
    <dialog aria-labelledby="written-report-title" className="dialog" ref={dialog} onClose={onClose}>
      <form
        className="stack"
        method="dialog"
        onSubmit={(event) => {
          event.preventDefault();
          void generate();
        }}
      >
        <h2 id="written-report-title">Written report</h2>
        <p className="panel-sub">Uses the filters on this page. The writing is drafted from totals only, never from individual rows.</p>
        <fieldset className="choice-group" disabled={busy}>
          <legend className="field-label">Audience</legend>
          {AUDIENCES.map((option) => (
            <label className="choice" key={option.value}>
              <input checked={audience === option.value} name="audience" type="radio" onChange={() => setAudience(option.value)} />
              <span>
                <strong>{option.label}</strong> <span className="panel-sub">{option.hint}</span>
              </span>
            </label>
          ))}
        </fieldset>
        <fieldset className="choice-group" disabled={busy}>
          <legend className="field-label">File type</legend>
          {FORMATS.map((option) => (
            <label className="choice" key={option.value}>
              <input checked={format === option.value} name="format" type="radio" onChange={() => setFormat(option.value)} />
              <span>{option.label}</span>
            </label>
          ))}
        </fieldset>
        {error && (
          <p className="alert alert-danger" role="alert">
            <Icon name="alert" />
            {error}
          </p>
        )}
        {busy && (
          <p className="panel-sub" role="status">
            Writing your report. This can take a few seconds…
          </p>
        )}
        <div className="row report-actions">
          <button className="btn btn-primary" disabled={busy} type="submit">
            <Icon name="reports" /> Generate
          </button>
          <button className="btn btn-secondary" type="button" onClick={() => dialog.current?.close()}>
            Cancel
          </button>
        </div>
      </form>
    </dialog>
  );
}
