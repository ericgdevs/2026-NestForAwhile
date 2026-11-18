import { useEffect, useState } from "react";

import {
  getReportOptions,
  getReportPreview,
  type ReportFilters,
  type ReportOptions,
  type ReportPreview,
} from "../api/client";
import ExportDataDialog from "../components/ExportDataDialog";
import Icon from "../components/Icon";
import WrittenReportDialog from "../components/WrittenReportDialog";

type Preset = "custom" | "donor" | "grant";

const DEBOUNCE_MS = 250; // wait for a pause in typing before asking the server again
const DAY_MS = 86_400_000;

// Seed labels read "DONOR-SYN-001"; the table and filters show "DONOR-001". Exports keep the stored label.
const shortLabel = (label: string) => label.replace("-SYN-", "-");

const daysAgo = (days: number) => new Date(Date.now() - days * DAY_MS).toISOString().slice(0, 10);

// Presets only fill in the filters; every filter stays editable afterwards.
const PRESETS: Record<Preset, { label: string; filters: () => ReportFilters }> = {
  custom: { label: "Custom", filters: () => ({}) },
  donor: { label: "Donor preset", filters: () => ({ attributed: "donor", date_from: daysAgo(30) }) },
  grant: { label: "Grant preset", filters: () => ({ attributed: "grant", date_from: daysAgo(90) }) },
};

export default function Reports() {
  const [preset, setPreset] = useState<Preset>("donor");
  const [filters, setFilters] = useState<ReportFilters>(PRESETS.donor.filters());
  const [options, setOptions] = useState<ReportOptions | null>(null);
  const [preview, setPreview] = useState<ReportPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [writing, setWriting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getReportOptions().then(setOptions).catch(() => setOptions({ donors: [], grants: [], categories: [] }));
  }, []);

  // The preview refetches as filters change; an older, slower answer never overwrites a newer one.
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    const timer = setTimeout(() => {
      getReportPreview(filters, controller.signal)
        .then((data) => {
          setPreview(data);
          setError("");
          setLoading(false);
        })
        .catch((reason: Error) => {
          if (reason.name === "AbortError") return;
          setError(reason.message);
          setLoading(false);
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [filters]);

  const choose = (next: Preset) => {
    setPreset(next);
    setFilters(PRESETS[next].filters());
  };
  const change = (key: keyof ReportFilters, value: string) => {
    setPreset("custom");
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const field = (key: keyof ReportFilters, label: string, type = "date") => (
    <div className="field">
      <label className="field-label" htmlFor={`report-${key}`}>
        {label}
      </label>
      <input
        className="input"
        id={`report-${key}`}
        min={type === "number" ? 1 : undefined}
        type={type}
        value={filters[key] ?? ""}
        onChange={(event) => change(key, event.target.value)}
      />
    </div>
  );
  const select = (key: keyof ReportFilters, label: string, choices: { value: string; label: string }[]) => (
    <div className="field">
      <label className="field-label" htmlFor={`report-${key}`}>
        {label}
      </label>
      <select className="input" id={`report-${key}`} value={filters[key] ?? ""} onChange={(event) => change(key, event.target.value)}>
        <option value="">Any</option>
        {choices.map((choice) => (
          <option key={choice.value} value={choice.value}>
            {choice.label}
          </option>
        ))}
      </select>
    </div>
  );

  const totals = preview?.totals;
  return (
    <main>
      <header className="page-head page-head-plain">
        <div>
          <h1>Reports</h1>
          <p>Anonymous visit data. Participants appear as codes, never names or contact details.</p>
        </div>
      </header>

      <section aria-label="Generate" className="panel stack">
        <h2 className="panel-title">Generate from these filters</h2>
        <div className="row report-actions">
          <button className="btn btn-primary" type="button" onClick={() => setWriting(true)}>
            <Icon name="reports" /> Generate Report
          </button>
          <button className="btn btn-secondary" type="button" onClick={() => setExporting(true)}>
            <Icon name="restock" /> Export Data
          </button>
        </div>
        <p className="panel-sub">Written reports (PDF or Word, with charts) are drafted from totals only, never from individual rows.</p>
      </section>

      <button
        aria-controls="report-filters"
        aria-expanded={filtersOpen}
        className="btn btn-secondary"
        style={{ marginTop: "1rem" }}
        type="button"
        onClick={() => setFiltersOpen((open) => !open)}
      >
        <Icon name="list" /> Filters and Search
      </button>

      {filtersOpen && (
      <section aria-label="Filters" className="panel stack" id="report-filters" style={{ marginTop: "1rem" }}>
        <div className="row report-actions" role="group" aria-label="Presets">
          {(Object.keys(PRESETS) as Preset[]).map((key) => (
            <button
              aria-pressed={preset === key}
              className={`btn btn-compact ${preset === key ? "btn-primary" : "btn-secondary"}`}
              key={key}
              type="button"
              onClick={() => choose(key)}
            >
              {PRESETS[key].label}
            </button>
          ))}
        </div>
        <div className="grid grid-2">
          {field("date_from", "From")}
          {field("date_to", "To")}
          {select("attributed", "Funding source", [
            { value: "donor", label: "Donor-attributed" },
            { value: "grant", label: "Grant-attributed" },
          ])}
          {select("donor_id", "Donor", (options?.donors ?? []).map((d) => ({ value: String(d.id), label: shortLabel(d.label) })))}
          {select("grant_id", "Grant", (options?.grants ?? []).map((g) => ({ value: String(g.id), label: shortLabel(g.label) })))}
          {select("category", "Product category", (options?.categories ?? []).map((c) => ({ value: c, label: c })))}
          {field("household_min", "Household size from", "number")}
          {field("household_max", "Household size to", "number")}
        </div>
      </section>
      )}

      {error && (
        <p className="alert alert-danger" role="alert" style={{ marginTop: "1rem" }}>
          <Icon name="alert" />
          {error}
        </p>
      )}

      <section aria-label="Preview" className="panel stack" style={{ marginTop: "1rem", opacity: loading ? 0.6 : 1 }}>
        <div className="panel-title panel-title-row">
          <h2>Preview</h2>
          <span aria-live="polite" className="panel-sub">
            {loading
              ? "Updating…"
              : totals && `${totals.visits} visits · ${totals.households} households · ${totals.items} items · ${totals.pounds} lb`}
          </span>
        </div>
        {!preview ? (
          <p className="empty">Loading data…</p>
        ) : preview.rows.length === 0 ? (
          <p className="empty">No visits match these filters.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Participant</th>
                  <th scope="col">Visit date</th>
                  <th className="num" scope="col">Household</th>
                  <th className="num" scope="col">Items</th>
                  <th className="num" scope="col">Pounds</th>
                  <th scope="col">Donors</th>
                  <th scope="col">Grants</th>
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, index) => (
                  <tr key={`${row.participant_id}-${row.visit_date}-${index}`}>
                    <td data-label="Participant"><strong>{row.participant_id}</strong></td>
                    <td data-label="Visit date">{row.visit_date}</td>
                    <td className="num" data-label="Household">{row.household_size}</td>
                    <td className="num" data-label="Items">{row.items}</td>
                    <td className="num" data-label="Pounds">{row.pounds}</td>
                    <td data-label="Donors">{row.donors.map(shortLabel).join(", ") || "—"}</td>
                    <td data-label="Grants">{row.grants.map(shortLabel).join(", ") || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {totals && preview && totals.visits > preview.rows.length && (
          <p className="panel-sub">Showing the newest {preview.rows.length} of {totals.visits} visits. Exports include every match.</p>
        )}
      </section>
    {exporting && <ExportDataDialog filters={filters} onClose={() => setExporting(false)} />}
    {writing && <WrittenReportDialog filters={filters} onClose={() => setWriting(false)} />}
    </main>
  );
}
