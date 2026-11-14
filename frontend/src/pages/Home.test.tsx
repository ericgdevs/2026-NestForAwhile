import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Home from "./Home";

vi.mock("../api/client", () => ({
  getRecommendations: vi.fn().mockResolvedValue([
    {
      product_id: 1,
      name: "Synthetic Oats",
      quantity: 2,
      status: "Approved",
      rationale: "This item matches the selected dietary profile.",
      aisle: "A1",
      shelf: "S1",
      bin: "B1",
    },
  ]),
}));

test("renders recommendation rationale, quantity, and safety status", async () => {
  render(<Home />);
  await waitFor(() => expect(screen.getByText("Synthetic Oats")).toBeInTheDocument());
  expect(screen.getByText(/matches the selected dietary profile/i)).toBeInTheDocument();
  expect(screen.getByText((_, element) => element?.textContent === "Suggested quantity: 2")).toBeInTheDocument();
  expect(screen.getByRole("status", { name: /good match/i })).toBeInTheDocument();
});
