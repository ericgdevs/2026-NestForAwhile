import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Recipes from "./Recipes";

vi.mock("../api/client", () => ({
  getRecipes: vi.fn().mockResolvedValue({
    used_fallback: true,
    recipes: [
      {
        title: "Simple pantry bowl",
        ingredients: [{ name: "Synthetic oats", product_id: 1 }],
        steps: ["Combine the available ingredients."],
      },
    ],
  }),
}));

test("renders recipes and fallback notice", async () => {
  render(<Recipes />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Simple pantry bowl" })).toBeInTheDocument());
  expect(screen.getByText(/rules-only recipe fallback/i)).toBeInTheDocument();
});
