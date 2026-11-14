import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Analytics from "./Analytics";
import Lots from "./Lots";
import Replenishment from "./Replenishment";

vi.mock("../api/client", () => ({
  getAnalytics: vi.fn().mockResolvedValue({
    families_served: 2,
    visits_completed: 3,
    pounds_distributed: 4,
    inventory_usage: 5,
    recommendation_adoption_rate: 0.5,
    waste_reduction: { expiring_soon_lots: 1, pounds_saved: 2 },
  }),
  getInventoryLots: vi.fn().mockResolvedValue([
    { lot_id: 1, product_id: 2, quantity: 3, expiration_date: "2026-11-20", expiring_soon: true },
  ]),
  getReplenishment: vi.fn().mockResolvedValue([
    { product_id: 2, name: "Synthetic Oats", quantity: 1, reorder_threshold: 5, aisle: "A", shelf: "1", bin: "1", priority: 20 },
  ]),
}));

test("renders inventory warning and replenishment item", async () => {
  render(<Lots />);
  render(<Replenishment />);
  expect(await screen.findByRole("alert")).toHaveTextContent(/expire/i);
  expect(await screen.findByText(/Synthetic Oats/)).toBeInTheDocument();
});

test("renders aggregate analytics", async () => {
  render(<Analytics />);
  expect(await screen.findByText("families served")).toBeInTheDocument();
  expect(screen.queryByText(/client|email/i)).not.toBeInTheDocument();
});
