import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import Reports from "./Reports";

const api = vi.hoisted(() => ({
  getReportOptions: vi.fn(),
  getReportPreview: vi.fn(),
  downloadReportData: vi.fn(),
  downloadWrittenReport: vi.fn(),
}));
vi.mock("../api/client", () => api);

const row = { participant_id: "P-1A2B3C4D", visit_date: "2026-03-10", household_size: 1, items: 3, pounds: 4.5, donors: ["DONOR-SYN-001"], grants: ["GRANT-SYN-002"] };
const preview = (rows = [row]) => ({ totals: { visits: rows.length, households: rows.length, items: 3, pounds: 4.5 }, rows });

beforeEach(() => {
  vi.clearAllMocks();
  api.getReportOptions.mockResolvedValue({ donors: [{ id: 1, label: "Synthetic Donor Co" }], grants: [], categories: ["Grains"] });
  api.getReportPreview.mockResolvedValue(preview());
  api.downloadReportData.mockResolvedValue(undefined);
  api.downloadWrittenReport.mockResolvedValue(undefined);
});

const openFilters = () => fireEvent.click(screen.getByRole("button", { name: /filters and search/i }));

test("donor and grant labels drop the SYN part", async () => {
  render(<Reports />);
  expect(await screen.findByText("DONOR-001")).toBeInTheDocument();
  expect(screen.getByText("GRANT-002")).toBeInTheDocument();
  expect(screen.queryByText(/SYN/)).not.toBeInTheDocument();
});

test("filters stay folded behind a button until opened", async () => {
  render(<Reports />);
  await screen.findByText("P-1A2B3C4D");
  expect(screen.queryByLabelText("Household size from")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /filters and search/i })).toHaveAttribute("aria-expanded", "false");
  openFilters();
  expect(screen.getByLabelText("Household size from")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /filters and search/i })).toHaveAttribute("aria-expanded", "true");
});

test("generate comes before the filters and the preview", async () => {
  render(<Reports />);
  await screen.findByText("P-1A2B3C4D");
  const generate = screen.getByRole("region", { name: "Generate" });
  expect(generate.compareDocumentPosition(screen.getByRole("region", { name: "Preview" })) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(generate.compareDocumentPosition(screen.getByRole("button", { name: /filters and search/i })) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

test("starts on the donor preset and shows anonymous rows with totals", async () => {
  render(<Reports />);
  expect(await screen.findByText("P-1A2B3C4D")).toBeInTheDocument();
  expect(api.getReportPreview.mock.calls[0][0]).toMatchObject({ attributed: "donor" });
  expect(screen.getByText(/1 visits · 1 households · 3 items · 4.5 lb/)).toBeInTheDocument();
  openFilters();
  expect(screen.getByRole("button", { name: "Donor preset" })).toHaveAttribute("aria-pressed", "true");
});

test("changing a filter refreshes the preview and switches to custom", async () => {
  render(<Reports />);
  await screen.findByText("P-1A2B3C4D");
  api.getReportPreview.mockResolvedValue(preview([]));
  openFilters();

  fireEvent.change(screen.getByLabelText("Household size from"), { target: { value: "5" } });

  expect(await screen.findByText("No visits match these filters.")).toBeInTheDocument();
  expect(api.getReportPreview).toHaveBeenLastCalledWith(expect.objectContaining({ household_min: "5" }), expect.anything());
  expect(screen.getByRole("button", { name: "Custom" })).toHaveAttribute("aria-pressed", "true");
});

test("the grant preset fills the filters and every filter stays editable", async () => {
  render(<Reports />);
  await screen.findByText("P-1A2B3C4D");
  openFilters();
  fireEvent.click(screen.getByRole("button", { name: "Grant preset" }));
  await waitFor(() => expect(api.getReportPreview).toHaveBeenLastCalledWith(expect.objectContaining({ attributed: "grant" }), expect.anything()));
  expect(screen.getByLabelText("Funding source")).toHaveValue("grant");
});

test("Export Data opens a pop-up to pick CSV or JSON and exports with the current filters", async () => {
  render(<Reports />);
  await screen.findByText("P-1A2B3C4D");
  expect(screen.queryByRole("button", { name: /download csv/i })).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Export Data" }));
  const dialog = screen.getByRole("dialog", { name: "Export data" });
  expect(within(dialog).getByRole("radio", { name: /csv/i })).toBeChecked();
  fireEvent.click(within(dialog).getByRole("button", { name: "Export" }));
  await waitFor(() => expect(api.downloadReportData).toHaveBeenCalledWith("csv", expect.objectContaining({ attributed: "donor" })));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Export Data" }));
  fireEvent.click(within(screen.getByRole("dialog")).getByRole("radio", { name: /json/i }));
  fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Export" }));
  await waitFor(() => expect(api.downloadReportData).toHaveBeenCalledWith("json", expect.anything()));
});

test("a failed export shows a clear message and keeps the pop-up open", async () => {
  api.downloadReportData.mockRejectedValue(new Error("Download failed with status 500"));
  render(<Reports />);
  await screen.findByText("P-1A2B3C4D");
  fireEvent.click(screen.getByRole("button", { name: "Export Data" }));
  const dialog = screen.getByRole("dialog");
  fireEvent.click(within(dialog).getByRole("button", { name: "Export" }));
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("Download failed with status 500");
});

const openWriter = async () => {
  render(<Reports />);
  await screen.findByText("P-1A2B3C4D");
  fireEvent.click(screen.getByRole("button", { name: "Generate Report" }));
  return screen.getByRole("dialog");
};

test("the written report pop-up asks for audience and file type, then downloads with the filters", async () => {
  const dialog = await openWriter();
  expect(within(dialog).getByRole("radio", { name: /donor/i })).toBeChecked();
  fireEvent.click(within(dialog).getByRole("radio", { name: /grant funder/i }));
  fireEvent.click(within(dialog).getByRole("radio", { name: "PDF" }));
  fireEvent.click(within(dialog).getByRole("button", { name: "Generate" }));

  await waitFor(() => expect(api.downloadWrittenReport).toHaveBeenCalledWith("grant", "pdf", expect.objectContaining({ attributed: "donor" })));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
});

test("'Both' and the general audience are offered", async () => {
  const dialog = await openWriter();
  fireEvent.click(within(dialog).getByRole("radio", { name: /general/i }));
  fireEvent.click(within(dialog).getByRole("radio", { name: /both/i }));
  fireEvent.click(within(dialog).getByRole("button", { name: "Generate" }));
  await waitFor(() => expect(api.downloadWrittenReport).toHaveBeenCalledWith("general", "both", expect.anything()));
});

test("cancel closes the pop-up without generating anything", async () => {
  const dialog = await openWriter();
  fireEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));
  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
  expect(api.downloadWrittenReport).not.toHaveBeenCalled();
});

test("a failed report shows a clear message and keeps the pop-up open to retry", async () => {
  api.downloadWrittenReport.mockRejectedValue(new Error("Download failed with status 500"));
  const dialog = await openWriter();
  fireEvent.click(within(dialog).getByRole("button", { name: "Generate" }));
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("Download failed with status 500");
  expect(within(dialog).getByRole("button", { name: "Generate" })).toBeEnabled();
});
