import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import ShoppingList from "./ShoppingList";

const recipe = { title: "Bean tacos", ingredients: [], steps: ["Warm the beans."] };
const lines = [
  { id: 1, text: "beans", product_id: 2, name: "Synthetic Black Beans", source: "recipe", recipe, ticked: false, in_stock: true, location: { aisle: "A2", shelf: "S2", bin: "B2" }, status: "Approved", not_for: [] },
  { id: 2, text: "unicorn milk", product_id: null, name: "unicorn milk", source: "you", recipe: null, ticked: false, in_stock: false, location: null },
];

const api = vi.hoisted(() => ({
  getShoppingList: vi.fn(),
  tickListLine: vi.fn(),
  deleteListLine: vi.fn(),
  parseShoppingList: vi.fn(),
  addToShoppingList: vi.fn(),
}));
vi.mock("../api/client", () => api);

test("shows locations, sources, and ticks a line", async () => {
  api.getShoppingList.mockResolvedValue({ items: lines });
  api.tickListLine.mockResolvedValue({ items: [{ ...lines[0], ticked: true }, lines[1]] });
  render(<ShoppingList />);

  expect(await screen.findByText("Aisle A2 · Shelf S2 · Bin B2")).toBeInTheDocument();
  expect(screen.getByText("For: Bean tacos")).toBeInTheDocument();
  expect(screen.getByText("You added")).toBeInTheDocument();
  expect(screen.getByText(/don't carry this today/)).toBeInTheDocument();
  expect(screen.getByText("Open recipe: Bean tacos")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("checkbox", { name: /Synthetic Black Beans/ }));
  await waitFor(() => expect(api.tickListLine).toHaveBeenCalledWith(1, true));
  await waitFor(() => expect(screen.getByText("left to find").parentElement).toHaveTextContent("1left to find"));
});

test("typed list is matched, reviewed, then added", async () => {
  api.getShoppingList.mockResolvedValue({ items: [] });
  api.parseShoppingList.mockResolvedValue({
    lines: [
      { text: "oats", product_id: 1, name: "Synthetic Rolled Oats", status: "Approved", location: null },
      { text: "caviar", product_id: null, name: null, status: null, location: null },
    ],
  });
  api.addToShoppingList.mockResolvedValue({ items: [] });
  render(<ShoppingList />);
  await screen.findByText(/your list is empty/i);

  fireEvent.change(screen.getByLabelText("Type or paste your list"), { target: { value: "oats\ncaviar" } });
  fireEvent.click(screen.getByRole("button", { name: "Find these items" }));
  fireEvent.click(await screen.findByRole("checkbox", { name: /caviar/ }));
  fireEvent.click(screen.getByRole("button", { name: "Add 1 to my list" }));

  await waitFor(() => expect(api.addToShoppingList).toHaveBeenCalledWith([{ text: "oats", product_id: 1 }]));
  expect(api.parseShoppingList).toHaveBeenCalledWith({ text: "oats\ncaviar" });
});
