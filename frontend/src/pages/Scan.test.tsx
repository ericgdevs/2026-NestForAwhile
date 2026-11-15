import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import Scan from "./Scan";

const api = vi.hoisted(() => ({
  scanProduct: vi.fn(),
  saveCartItem: vi.fn().mockResolvedValue({ items: [] }),
  getRecipes: vi.fn(),
  saveRecipe: vi.fn().mockResolvedValue({}),
  addRecipeToList: vi.fn().mockResolvedValue({ items: [] }),
}));

vi.mock("../components/BarcodeScanner", () => ({ default: () => <div>Camera scanner</div> }));
vi.mock("../api/client", () => api);

const oats = {
  product_id: 1,
  sku: "SYN-OATS-001",
  barcode: "000000000001",
  name: "Synthetic Oats",
  image_url: null,
  sodium_mg: 0,
  sugar_g: 1,
  sat_fat_g: 0.5,
  potassium_mg: 120,
  status: "Approved",
  explanation: "This item matches the selected dietary profile.",
  not_for: [],
  swaps: [],
};

const recipe = {
  title: "Oat porridge",
  cuisine: "American",
  ingredients: [{ name: "Synthetic Oats", product_id: 1 }],
  steps: ["Simmer."],
};

beforeEach(() => {
  api.getRecipes.mockResolvedValue({ recipes: [recipe], used_fallback: false });
});

function scanFor(value: string) {
  fireEvent.change(screen.getByLabelText("SKU or barcode"), { target: { value } });
  fireEvent.click(screen.getByRole("button", { name: "Check" }));
}

test("supports manual SKU lookup and shows recipes for the item", async () => {
  api.scanProduct.mockResolvedValue(oats);
  render(<Scan />);
  scanFor("SYN-OATS-001");
  await waitFor(() => expect(screen.getByRole("heading", { name: "Synthetic Oats" })).toBeInTheDocument());
  expect(screen.getByText(/matches the selected dietary profile/i)).toBeInTheDocument();
  expect(api.getRecipes).toHaveBeenCalledWith({ scanned_product_id: 1 });

  fireEvent.click(await screen.findByRole("button", { name: "Save: Oat porridge" }));
  fireEvent.click(screen.getByRole("button", { name: "Add to list: Oat porridge" }));
  await waitFor(() => expect(api.addRecipeToList).toHaveBeenCalledWith(recipe, 1));
  expect(api.saveRecipe).toHaveBeenCalledWith(recipe, 1);
  expect(await screen.findByRole("button", { name: "On your list: Oat porridge" })).toBeDisabled();
});

test("Red scan shows who it is not for, swaps, and confirms before adding", async () => {
  api.scanProduct.mockResolvedValue({
    ...oats,
    product_id: 4,
    name: "Synthetic Nut Crackers",
    status: "Restricted",
    not_for: [{ nickname: "Little one", reason: "Nut Allergy" }],
    allergy_match: true,
    swaps: [{ product_id: 1, name: "Synthetic Oats", status: "Approved", not_for: [], aisle: "A1", shelf: "S1", bin: "B1" }],
  });
  const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(false).mockReturnValueOnce(true);
  render(<Scan />);
  scanFor("SYN-CRACK-001");

  expect(await screen.findByText("Little one")).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Safer swaps" })).toHaveTextContent("Aisle A1 · Shelf S1 · Bin B1");

  fireEvent.click(screen.getByRole("button", { name: "Add to cart" }));
  expect(api.saveCartItem).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Add to cart" }));
  await waitFor(() => expect(api.saveCartItem).toHaveBeenCalledWith(4, 1));
  expect(confirm).toHaveBeenCalledTimes(2);
});
