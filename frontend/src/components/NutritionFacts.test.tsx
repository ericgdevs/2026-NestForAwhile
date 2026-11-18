import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import NutritionFacts from "./NutritionFacts";

test("shows the full label with % Daily Value", () => {
  render(
    <NutritionFacts
      facts={{
        serving_size_g: 55, calories: 230, total_fat_g: 8, sat_fat_g: 1, trans_fat_g: 0, cholesterol_mg: 0,
        sodium_mg: 160, carbs_g: 37, fiber_g: 4, sugar_g: 12, added_sugar_g: 10, protein_g: 3,
        vitamin_d_mcg: 2, calcium_mg: 260, iron_mg: 8, potassium_mg: 240,
      }}
    />,
  );
  expect(screen.getByText("Calories").nextSibling).toHaveTextContent("230");
  expect(screen.getByText("Serving size").nextSibling).toHaveTextContent("55g");
  expect(screen.getByText("Total Fat").closest("div")).toHaveTextContent("10%");
  expect(screen.getByText("Includes Added Sugars").closest("div")).toHaveTextContent("20%");
  expect(screen.getByText("Calcium").closest("div")).toHaveTextContent("20%");
  expect(screen.getByText("Protein").closest("div")).toHaveTextContent("3g");
  expect(screen.getByText(/% Daily Value \(DV\)/)).toBeInTheDocument();
});

test("leaves off any nutrient with no value, but keeps a real zero", () => {
  render(<NutritionFacts facts={{ calories: null, carbs_g: null, sodium_mg: 0, sugar_g: undefined, sat_fat_g: null }} />);
  expect(screen.getByText("Sodium").closest("div")).toHaveTextContent("0mg0%");
  for (const label of ["Calories", "Serving size", "Total Fat", "Total Carbohydrate", "Total Sugars", "Saturated Fat", "Iron"]) {
    expect(screen.queryByText(label)).not.toBeInTheDocument();
  }
});

test("no footnote when there is nothing with a daily value", () => {
  render(<NutritionFacts facts={{ calories: 100 }} />);
  expect(screen.queryByText(/Daily Value/)).not.toBeInTheDocument();
});
