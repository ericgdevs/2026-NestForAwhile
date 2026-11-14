import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

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
