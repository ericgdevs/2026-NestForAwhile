import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import RecipeGroups, { groupByCuisine } from "./RecipeGroups";

const recipe = (title: string, cuisine?: string) => ({
  title,
  cuisine,
  ingredients: [{ name: "Synthetic rice", product_id: 1 }],
  steps: ["Cook."],
});

test("groups by cuisine in API order and falls back to one suggested group", () => {
  const groups = groupByCuisine([recipe("A", "Mexican"), recipe("B", "Italian"), recipe("C", "Mexican"), recipe("D")]);
  expect(groups.map(([name, items]) => [name, items.map((item) => item.title)])).toEqual([
    ["Mexican", ["A", "C"]],
    ["Italian", ["B"]],
    ["Suggested for you", ["D"]],
  ]);
});

test("shows cuisine tabs with a top pick per cuisine", () => {
  render(<RecipeGroups recipes={[recipe("Bean tacos", "Mexican"), recipe("Rice bowl", "Mexican"), recipe("Tomato pasta", "Italian")]} />);
  expect(screen.getByRole("heading", { name: "Bean tacos" }).closest("article")).toHaveTextContent("Top pick");
  expect(screen.queryByRole("heading", { name: "Tomato pasta" })).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Italian" }));
  expect(screen.getByRole("heading", { name: "Tomato pasta" }).closest("article")).toHaveTextContent("Top pick");
});

test("shows no tabs when the API sends no cuisine", () => {
  render(<RecipeGroups recipes={[recipe("Pantry bowl")]} />);
  expect(screen.queryByRole("group", { name: "Cuisines" })).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Pantry bowl" })).toBeInTheDocument();
});

test("Add to list confirms what was added and what was already in the cart, with a link to the list", async () => {
  const onAddToList = vi.fn().mockResolvedValue({
    added: [
      { name: "Synthetic Black Beans", location: { aisle: "A2", shelf: "S2", bin: "B2" } },
      { name: "Synthetic Rolled Oats", location: { aisle: "A1", shelf: "S1", bin: "B1" } },
      { name: "salt", location: null },
    ],
    blocked: [],
    in_cart: 2,
    already_on_list: 0,
  });
  render(<RecipeGroups actions={{ onAddToList }} recipes={[recipe("Bean tacos")]} />);
  fireEvent.click(screen.getByRole("button", { name: "Add to list: Bean tacos" }));

  expect(await screen.findByText(/Added 3 items to your list \(2 already in your cart\)/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "View your list" })).toHaveAttribute("href", "/list");
  expect(screen.getByText("Aisle A2 · S2 · B2")).toBeInTheDocument();
});

test("a restricted ingredient is not added: the reason and an in-stock swap are shown", async () => {
  const onSave = vi.fn().mockResolvedValue({
    added: [],
    blocked: [
      {
        name: "Nut crackers",
        not_for: [{ nickname: "Little one", reason: "nut allergy" }],
        swaps: [{ product_id: 9, name: "Seed crackers", status: "Approved", aisle: "A4", shelf: "S1", bin: "B1" }],
      },
    ],
    in_cart: 0,
    already_on_list: 1,
  });
  render(<RecipeGroups actions={{ onSave }} recipes={[recipe("Cracker plate")]} />);
  fireEvent.click(screen.getByRole("button", { name: "Save: Cracker plate" }));

  expect(await screen.findByText(/Nothing new to add to your list \(1 already on your list\)/)).toBeInTheDocument();
  expect(screen.getByRole("alert")).toHaveTextContent(/Not added: Nut crackers.*Not for Little one: nut allergy/);
  expect(screen.getByRole("button", { name: /Add Seed crackers instead/ })).toBeInTheDocument();
});
