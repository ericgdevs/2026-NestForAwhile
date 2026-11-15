import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Analytics from "./Analytics";

vi.mock("../api/client", () => ({
  getAnalytics: vi.fn().mockResolvedValue({
    families_served: 31,
    visits_completed: 52,
    pounds_distributed: 640.5,
    inventory_usage: 1275,
    recommendation_adoption_rate: 0.483,
    waste_reduction: { expiring_soon_lots: 0, pounds_saved: 86 },
  }),
}));

test("shows totals and waste reduction as stat cards", async () => {
  render(<Analytics />);
  expect(await screen.findByRole("region", { name: "Totals to date" })).toBeInTheDocument();
  expect(screen.getByText("Families served").nextSibling).toHaveTextContent("31");
  expect(screen.getByText("Units given out").nextSibling).toHaveTextContent("1,275");
  expect(screen.getByText("Picks taken from recommendations").nextSibling).toHaveTextContent("48%");
  expect(screen.getByText("Pounds saved from near-expiry lots").nextSibling).toHaveTextContent("86");
  // No expiring lots: the warning card reads as fine instead of amber.
  expect(screen.getByText("Lots expiring within 7 days").closest(".stat-card")).toHaveClass("stat-ok");
});
