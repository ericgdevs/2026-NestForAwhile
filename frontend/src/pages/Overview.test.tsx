import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Overview, { leadFact } from "./Overview";

const role = vi.hoisted(() => ({ current: "Warehouse Staff" }));

vi.mock("../lib/auth", () => ({ useAuth: () => ({ user: { role: role.current } }) }));
vi.mock("../api/client", () => ({
  getCapacity: vi.fn().mockResolvedValue({ Active_Floor_Shoppers: 7 }),
  getInventoryLots: vi.fn().mockResolvedValue([
    { lot_id: 1, product_id: 2, quantity: 3, expiration_date: "2026-11-20", expiring_soon: true },
    { lot_id: 2, product_id: 2, quantity: 9, expiration_date: "2027-01-20", expiring_soon: false },
  ]),
  getReplenishment: vi.fn().mockResolvedValue([]),
  getAnalytics: vi.fn().mockResolvedValue({
    families_served: 31,
    visits_completed: 52,
    pounds_distributed: 640,
    inventory_usage: 275,
    recommendation_adoption_rate: 0.5,
    waste_reduction: { expiring_soon_lots: 4, pounds_saved: 3 },
  }),
}));

test("the first non-zero action item leads, otherwise the first fact", () => {
  const words = { one: "x", many: "xs" };
  const lots = { label: "Lots", value: 0, href: "/lots", ...words };
  const low = { label: "Low", value: 2, href: "/replenishment", ...words };
  const shoppers = { label: "Shoppers", value: 5, ...words };
  expect(leadFact([lots, low, shoppers])).toBe(low);
  expect(leadFact([lots, { ...low, value: 0 }, shoppers])).toBe(lots);
  expect(leadFact([])).toBeUndefined();
});

test("warehouse roles see the expiring-lots warning and shopper count", async () => {
  render(<Overview />);
  expect(await screen.findByRole("alert")).toHaveTextContent("1 lot expires within seven days");
  expect(await screen.findByText("7")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Lots expiring within 7 days" })).toHaveAttribute("href", "/lots");
  expect(screen.getByText("lot expiring within 7 days")).toBeInTheDocument();
});

test("volunteers see shoppers only", async () => {
  role.current = "Volunteer";
  render(<Overview />);
  expect((await screen.findAllByText("7")).length).toBeGreaterThan(0);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.queryByText(/below threshold/i)).not.toBeInTheDocument();
});

test("directors see anonymized totals instead of floor and stock", async () => {
  role.current = "Director";
  render(<Overview />);
  expect(await screen.findByRole("heading", { name: "Totals to date" })).toBeInTheDocument();
  expect(screen.getByText("families served to date")).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText("Visits completed").nextSibling).toHaveTextContent("52"));
  expect(screen.getByText("Lots expiring within 7 days").nextSibling).toHaveTextContent("4");
  expect(screen.queryByText(/shoppers on the floor/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/Your screens are in the menu/)).not.toBeInTheDocument();
});

test("warning colours only show when there is something to act on", async () => {
  role.current = "Warehouse Staff";
  render(<Overview />);
  const expiring = await screen.findByRole("link", { name: "Lots expiring within 7 days" });
  await waitFor(() => expect(expiring.closest(".stat-card")).toHaveClass("stat-warn"));
  expect(screen.getByRole("link", { name: "Items below threshold" }).closest(".stat-card")).toHaveClass("stat-ok");
});
