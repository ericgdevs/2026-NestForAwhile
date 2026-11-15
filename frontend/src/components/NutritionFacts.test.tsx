import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import NutritionFacts from "./NutritionFacts";

const base = { sodium_mg: 140, sugar_g: 2, sat_fat_g: 1, potassium_mg: null };

test("shows calories and total carbs when the scan sends them", () => {
  render(<NutritionFacts facts={{ ...base, calories: 164, carbs_g: 6.1 }} />);
  expect(screen.getByText("Calories").nextSibling).toHaveTextContent("164");
  expect(screen.getByText("Total carbs").nextSibling).toHaveTextContent("6.1 g");
});

test("says Not available when calories or carbs are unknown", () => {
  render(<NutritionFacts facts={{ ...base, calories: null, carbs_g: null }} />);
  expect(screen.getByText("Calories").nextSibling).toHaveTextContent("Not available");
  expect(screen.getByText("Total carbs").nextSibling).toHaveTextContent("Not available");
});

test("leaves the rows out when the data has no calorie or carb fields (cart)", () => {
  render(<NutritionFacts facts={base} />);
  expect(screen.queryByText("Calories")).not.toBeInTheDocument();
  expect(screen.queryByText("Total carbs")).not.toBeInTheDocument();
});
