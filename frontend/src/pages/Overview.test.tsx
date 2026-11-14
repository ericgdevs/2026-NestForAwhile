import { render, screen } from "@testing-library/react";
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
