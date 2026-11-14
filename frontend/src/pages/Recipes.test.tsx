import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Recipes from "./Recipes";

const api = vi.hoisted(() => ({
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
  getSavedRecipes: vi.fn().mockResolvedValue([
    { id: 9, title: "Bean tacos", cuisine: "Mexican", ingredients: [{ name: "Beans", product_id: 2 }], steps: ["Warm."] },
  ]),
  deleteSavedRecipe: vi.fn().mockResolvedValue(undefined),
  saveRecipe: vi.fn(),
  addRecipeToList: vi.fn(),
}));

vi.mock("../api/client", () => api);

test("renders cart recipes and the fallback notice", async () => {
  render(<Recipes />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Simple pantry bowl" })).toBeInTheDocument());
  expect(screen.getByText(/rules-only recipe fallback/i)).toBeInTheDocument();
});

test("shows saved recipes and deletes one", async () => {
  render(<Recipes />);
  fireEvent.click(await screen.findByRole("button", { name: "Delete: Bean tacos" }));
  await waitFor(() => expect(api.deleteSavedRecipe).toHaveBeenCalledWith(9));
  expect(await screen.findByText(/no saved recipes yet/i)).toBeInTheDocument();
});
