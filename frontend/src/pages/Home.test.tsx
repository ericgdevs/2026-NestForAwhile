import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Home from "./Home";

vi.mock("../components/BarcodeScanner", () => ({ default: () => <div>Camera scanner</div> }));
vi.mock("../api/client", () => ({
  getRecommendations: vi.fn().mockResolvedValue([
    {
      product_id: 1,
      name: "Synthetic Oats",
      quantity: 2,
      status: "Capped",
      rationale: "This item matches the selected dietary profile.",
      not_for: [{ nickname: "Little one", reason: "Nut Allergy" }],
      allergy_match: true,
      aisle: "A1",
      shelf: "S1",
      bin: "B1",
    },
  ]),
  saveCartItem: vi.fn(),
}));

test("renders recommendation rationale, quantity, safety status, and who it is not for", async () => {
  render(<Home householdSize={2} />);
  await waitFor(() => expect(screen.getByText("Synthetic Oats")).toBeInTheDocument());
  expect(screen.getByText(/matches the selected dietary profile/i)).toBeInTheDocument();
  expect(screen.getByText((_, element) => element?.textContent === "Suggested quantity: 2")).toBeInTheDocument();
  expect(screen.getByRole("status", { name: /please check/i })).toBeInTheDocument();
  expect(screen.getByText("Little one")).toBeInTheDocument();
  expect(screen.getByText(/people in your household/).closest(".figure")).toHaveTextContent("2people in your household");
  expect(screen.getByRole("region", { name: "Scan a product" })).toBeInTheDocument();
});
