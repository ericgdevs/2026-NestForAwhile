import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useEffect } from "react";
import { expect, test, vi } from "vitest";

import VisitGate from "./VisitGate";

const api = vi.hoisted(() => ({
  getVisit: vi.fn(),
  checkIn: vi.fn(),
  claimQueue: vi.fn().mockResolvedValue({ Shopping_Session_Token: "tok" }),
  getSavedRecipes: vi.fn().mockResolvedValue([]),
}));
vi.mock("../api/client", () => api);

const shop = <h1>Shopping screen</h1>;

test("shows shopping screens only while shopping", async () => {
  api.getVisit.mockResolvedValue({ status: "shopping", Shopping_Session_Token: "tok" });
  render(<VisitGate>{shop}</VisitGate>);
  expect(await screen.findByText("Shopping screen")).toBeInTheDocument();
});

test("queued clients see their place in line and come in when ready", async () => {
  api.getVisit
    .mockResolvedValueOnce({ status: "queued", queue_status: "ready", position: null, message: "Your turn is ready." })
    .mockResolvedValue({ status: "shopping", Shopping_Session_Token: "tok" });
  render(<VisitGate>{shop}</VisitGate>);
  fireEvent.click(await screen.findByRole("button", { name: "Come in" }));
  expect(await screen.findByText("Shopping screen")).toBeInTheDocument();
  expect(api.claimQueue).toHaveBeenCalled();
});

test("after checkout the phone shows Visit complete and can start a new visit", async () => {
  api.getVisit.mockResolvedValue({ status: "complete", receipt: { checkout_id: 42, total_lb: 3.5, completed_at: "2026-11-14T20:00:00" } });
  api.checkIn.mockResolvedValue({ status: "shopping", Shopping_Session_Token: "tok2" });
  render(<VisitGate>{shop}</VisitGate>);
  expect(await screen.findByRole("heading", { name: "Visit complete" })).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent("Receipt #42");
  fireEvent.click(screen.getByRole("button", { name: "Start a new visit" }));
  expect(await screen.findByText("Shopping screen")).toBeInTheDocument();
});

test("Check again lets an approved client start shopping without signing in again", async () => {
  api.getVisit.mockResolvedValue({ status: "awaiting_approval" });
  api.checkIn.mockResolvedValueOnce({ status: "awaiting_approval" }).mockResolvedValueOnce({ status: "shopping", Shopping_Session_Token: "tok" });
  render(<VisitGate>{shop}</VisitGate>);
  fireEvent.click(await screen.findByRole("button", { name: "Check again" }));
  expect(await screen.findByText(/not approved yet/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Check again" }));
  await waitFor(() => expect(screen.getByText("Shopping screen")).toBeInTheDocument());
});

test("falls back to the normal screens if the visit service is unavailable", async () => {
  api.getVisit.mockRejectedValue(new Error("404"));
  render(<VisitGate>{shop}</VisitGate>);
  expect(await screen.findByText("Shopping screen")).toBeInTheDocument();
});

test("the page behind the gate starts loading while the visit is still being checked, then shows without remounting", async () => {
  let resolveVisit: (value: unknown) => void = () => undefined;
  api.getVisit.mockReturnValue(new Promise((resolve) => (resolveVisit = resolve)));
  let mounts = 0;
  function Page() {
    useEffect(() => void (mounts += 1), []);
    return <h1>Shopping screen</h1>;
  }
  render(
    <VisitGate>
      <Page />
    </VisitGate>,
  );
  expect(screen.getByText("Checking your visit…")).toBeInTheDocument();
  expect(screen.getByText("Shopping screen")).not.toBeVisible(); // mounted (fetching) but hidden

  resolveVisit({ status: "shopping", Shopping_Session_Token: "tok" });
  await waitFor(() => expect(screen.getByText("Shopping screen")).toBeVisible());
  expect(mounts).toBe(1);
});

test("a client who is not shopping never sees the page behind the gate", async () => {
  api.getVisit.mockResolvedValue({ status: "none" });
  render(<VisitGate>{shop}</VisitGate>);
  await waitFor(() => expect(screen.queryByText("Checking your visit…")).not.toBeInTheDocument());
  expect(screen.queryByText("Shopping screen")).not.toBeInTheDocument();
});
