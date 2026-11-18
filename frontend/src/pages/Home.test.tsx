import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Home from "./Home";

const pick = vi.hoisted(() => (product_id: number, name: string) => ({
  product_id,
  name,
  quantity: 2,
  status: "Approved",
  rationale: "Fits your household.",
  not_for: [],
  allergy_match: false,
  aisle: "A1",
  shelf: "S1",
  bin: "B1",
}));

vi.mock("../components/BarcodeScanner", () => ({ default: () => <div>Camera scanner</div> }));
vi.mock("../api/client", () => ({
  getRecommendations: vi.fn().mockResolvedValue([
    { ...pick(1, "Synthetic Oats"), rationale: "This item matches the selected dietary profile." },
    { ...pick(2, "Capped Item"), status: "Capped" },
    { ...pick(3, "Allergen Item"), allergy_match: true },
    { ...pick(4, "Flagged Item"), not_for: [{ nickname: "Little one", reason: "Nut Allergy" }] },
    ...Array.from({ length: 12 }, (_, i) => pick(10 + i, `Extra Item ${i}`)),
  ]),
  saveCartItem: vi.fn(),
  getShoppingList: vi.fn().mockResolvedValue({
    items: [
      { id: 1, ticked: false },
      { id: 2, ticked: true },
      { id: 3, ticked: false },
    ],
  }),
  parseShoppingList: vi.fn().mockResolvedValue({
    lines: [{ text: "oats", name: "Synthetic Oats", product_id: 1, status: "Approved", not_for: [], swaps: [] }],
  }),
  addToShoppingList: vi.fn(),
  scanProduct: vi.fn(),
  getHousehold: vi.fn().mockResolvedValue({
    members: [
      { nickname: "Grandpa", age: 71, restrictions: ["Low Sodium"], allergies: [], conditions: ["I10"] },
      { nickname: "Kiddo", age: 6, restrictions: [], allergies: ["Nut Allergy"], conditions: [] },
      { nickname: "Person 3", age: null, restrictions: [], allergies: [], conditions: [] },
    ],
  }),
}));

test("renders recommendation rationale, quantity, safety status, and who it is not for", async () => {
  render(<Home householdSize={2} />);
  await waitFor(() => expect(screen.getByText("Synthetic Oats")).toBeInTheDocument());
  expect(screen.getByText(/matches the selected dietary profile/i)).toBeInTheDocument();
  expect(screen.getAllByText((_, element) => element?.textContent === "Suggested quantity: 2")).toHaveLength(12);
  expect(screen.getAllByRole("status", { name: /good match/i })).toHaveLength(12);
  expect(screen.getByText(/people in your household/).closest(".figure")).toHaveTextContent("2people in your household");
  expect(screen.getByRole("region", { name: "Scan a product" })).toBeInTheDocument();
});

test("recommends at most 12 items, only clean good matches", async () => {
  render(<Home householdSize={2} />);
  await screen.findByText("Synthetic Oats");
  expect(screen.getAllByRole("article")).toHaveLength(12);
  for (const name of ["Capped Item", "Allergen Item", "Flagged Item", "Extra Item 11"]) {
    expect(screen.queryByText(name)).not.toBeInTheDocument();
  }
});

test("grocery list widget shows what is left, links to the list, and reviews typed items", async () => {
  render(<Home householdSize={2} />);
  const widget = await screen.findByRole("region", { name: "Grocery list" });
  await waitFor(() => expect(widget).toHaveTextContent("2 items left to find"));
  expect(screen.getByRole("link", { name: /open full list/i })).toHaveAttribute("href", "/list");
  expect(widget).not.toHaveTextContent("Scan to add");

  fireEvent.change(screen.getByLabelText("Type or paste your list"), { target: { value: "oats" } });
  fireEvent.click(screen.getByRole("button", { name: "Find these items" }));
  expect(await screen.findByText(/We matched: Synthetic Oats/)).toBeInTheDocument();
});

test("household widget lists diet choices and allergies, never medical conditions", async () => {
  render(<Home householdSize={3} />);
  const widget = await screen.findByRole("region", { name: "Your household" });
  await waitFor(() => expect(widget).toHaveTextContent("Grandpa"));
  expect(widget).toHaveTextContent("Low Sodium");
  expect(widget).toHaveTextContent("Nut allergy");
  expect(widget).toHaveTextContent("No restrictions");
  expect(widget).not.toHaveTextContent("I10");
  expect(screen.getByRole("link", { name: /edit household/i })).toHaveAttribute("href", "/profile");
});
