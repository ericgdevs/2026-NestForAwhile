import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import ShoppingList from "./ShoppingList";

const recipe = { title: "Bean tacos", ingredients: [], steps: ["Warm the beans."] };
const lines = [
  { id: 1, text: "beans", product_id: 2, name: "Synthetic Black Beans", source: "recipe", recipes: [recipe], ticked: false, in_stock: true, location: { aisle: "A2", shelf: "S2", bin: "B2" }, status: "Approved", not_for: [] },
  { id: 2, text: "unicorn milk", product_id: null, name: "unicorn milk", source: "you", recipes: [], ticked: false, in_stock: false, location: null },
];

const api = vi.hoisted(() => ({
  getShoppingList: vi.fn(),
  tickListLine: vi.fn(),
  deleteListLine: vi.fn(),
  parseShoppingList: vi.fn(),
  addToShoppingList: vi.fn(),
}));
beforeEach(() => vi.clearAllMocks());
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

test("one line shows every recipe it is for", async () => {
  const chili = { title: "Bean chili", ingredients: [], steps: ["Simmer."] };
  api.getShoppingList.mockResolvedValue({ items: [{ ...lines[0], source: "you", recipes: [recipe, chili] }] });
  render(<ShoppingList />);
  expect(await screen.findByText("For: Bean chili")).toBeInTheDocument();
  expect(screen.getByText("For: Bean tacos")).toBeInTheDocument();
  expect(screen.getByText("You added")).toBeInTheDocument();
  expect(screen.getAllByText(/^Open recipe:/)).toHaveLength(2);
});

const salty = {
  text: "salty soup",
  product_id: 5,
  name: "Salty Soup",
  status: "Restricted",
  not_for: [{ nickname: "Person 1", reason: "too much sodium" }],
  location: null,
  swaps: [{ product_id: 6, name: "Low Sodium Soup", status: "Approved", not_for: [], aisle: "A3", shelf: "S1", bin: "B1" }],
};

test("review: restricted item warns and offers a swap; the swap is added only after confirming", async () => {
  api.getShoppingList.mockResolvedValue({ items: [] });
  api.parseShoppingList.mockResolvedValue({ lines: [salty, { text: "caviar", product_id: null, name: null, status: null, location: null }] });
  api.addToShoppingList.mockResolvedValue({ items: [] });
  render(<ShoppingList />);
  await screen.findByText(/your list is empty/i);

  fireEvent.change(screen.getByLabelText("Type or paste your list"), { target: { value: "salty soup\ncaviar" } });
  fireEvent.click(screen.getByRole("button", { name: "Find these items" }));

  expect(await screen.findByText(/isn't recommended for anyone/i)).toBeInTheDocument();
  expect(screen.getByText(/We don't carry this/)).toBeInTheDocument();
  expect(api.addToShoppingList).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole("button", { name: /Use Low Sodium Soup instead/ }));
  fireEvent.click(screen.getByRole("button", { name: "Remove caviar" }));
  fireEvent.click(screen.getByRole("button", { name: "Add 1 to my list" }));

  await waitFor(() => expect(api.addToShoppingList).toHaveBeenCalledWith([{ text: "Low Sodium Soup", product_id: 6 }]));
});

test("review: editing a row's text matches it again", async () => {
  api.getShoppingList.mockResolvedValue({ items: [] });
  api.parseShoppingList
    .mockResolvedValueOnce({ lines: [{ text: "blak beans", product_id: null, name: null, status: null, location: null }] })
    .mockResolvedValueOnce({ lines: [{ text: "black beans", product_id: 2, name: "Synthetic Black Beans", status: "Approved", location: null }] });
  render(<ShoppingList />);
  await screen.findByText(/your list is empty/i);
  fireEvent.change(screen.getByLabelText("Type or paste your list"), { target: { value: "blak beans" } });
  fireEvent.click(screen.getByRole("button", { name: "Find these items" }));

  const input = await screen.findByLabelText("Item 1");
  fireEvent.change(input, { target: { value: "black beans" } });
  fireEvent.blur(input);

  expect(await screen.findByText(/We matched: Synthetic Black Beans/)).toBeInTheDocument();
  expect(api.parseShoppingList).toHaveBeenLastCalledWith({ text: "black beans" });
});

test("a photo the model can't read shows the server's clear message", async () => {
  api.getShoppingList.mockResolvedValue({ items: [] });
  api.parseShoppingList.mockRejectedValue(new Error("We can't read photos right now. Please type your list instead."));
  render(<ShoppingList />);
  await screen.findByText(/your list is empty/i);
  fireEvent.change(screen.getByLabelText("Type or paste your list"), { target: { value: "oats" } });
  fireEvent.click(screen.getByRole("button", { name: "Find these items" }));
  expect(await screen.findByRole("status")).toHaveTextContent(/type your list instead/i);
});

test("two lines that match the same product become one review row", async () => {
  api.getShoppingList.mockResolvedValue({ items: [] });
  const oats = { product_id: 1, name: "Synthetic Rolled Oats", status: "Approved", location: null };
  api.parseShoppingList.mockResolvedValue({ lines: [{ text: "oats", ...oats }, { text: "rolled oats", ...oats }] });
  api.addToShoppingList.mockResolvedValue({ items: [] });
  render(<ShoppingList />);
  await screen.findByText(/your list is empty/i);
  fireEvent.change(screen.getByLabelText("Type or paste your list"), { target: { value: "oats\nrolled oats" } });
  fireEvent.click(screen.getByRole("button", { name: "Find these items" }));

  expect(await screen.findAllByLabelText(/^Item \d/)).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Add 1 to my list" }));
  await waitFor(() => expect(api.addToShoppingList).toHaveBeenCalledWith([{ text: "oats", product_id: 1 }]));
});

test("a kept item we don't carry is added as a plain note, with no safety status", async () => {
  api.getShoppingList.mockResolvedValue({ items: [] });
  api.parseShoppingList.mockResolvedValue({ lines: [{ text: "pizza", product_id: null, name: null, status: null, location: null }] });
  api.addToShoppingList.mockResolvedValue({ items: [] });
  render(<ShoppingList />);
  await screen.findByText(/your list is empty/i);
  fireEvent.change(screen.getByLabelText("Type or paste your list"), { target: { value: "pizza" } });
  fireEvent.click(screen.getByRole("button", { name: "Find these items" }));

  expect(await screen.findByText(/go on your list as a note/)).toBeInTheDocument();
  expect(screen.queryByRole("status", { name: /Good match/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Add 1 to my list" }));
  await waitFor(() =>
    expect(api.addToShoppingList).toHaveBeenCalledWith([{ text: "pizza — not stocked today", product_id: null, note: true }]),
  );
});
