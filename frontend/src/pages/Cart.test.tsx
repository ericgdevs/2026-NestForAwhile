import { render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Cart from "./Cart";

const { getCart } = vi.hoisted(() => ({
  getCart: vi.fn().mockResolvedValue({
    items: [{ product_id: 1, name: "Synthetic Oats", quantity: 2, from_recommendation: true }],
  }),
}));

vi.mock("../api/client", () => ({
  getCart,
  saveCartItem: vi.fn(),
  deleteCartItem: vi.fn(),
}));

test("renders cart items and recommendation marker", async () => {
  render(<Cart />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Your cart" })).toBeInTheDocument());
  expect(screen.getByText("Synthetic Oats")).toBeInTheDocument();
  expect(screen.getByText(/recommended for you/i)).toBeInTheDocument();
});
