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

test("shows nutrition facts and status when the cart API sends them", async () => {
  getCart.mockResolvedValueOnce({
    items: [
      {
        product_id: 2,
        name: "Synthetic Beans",
        quantity: 3,
        from_recommendation: false,
        sku: "SYN-BEANS-001",
        status: "Capped",
        sodium_mg: 420,
        sugar_g: 1,
        sat_fat_g: null,
        potassium_mg: 300,
      },
    ],
  });
  render(<Cart />);
  expect(await screen.findByText("420mg")).toBeInTheDocument();
  expect(screen.getByRole("status", { name: /please check/i })).toBeInTheDocument();
  expect(screen.getByText((_, element) => element?.textContent === "Quantity in cart: 3")).toBeInTheDocument();
});

test("says nutrition is not available until the API sends it", async () => {
  render(<Cart />);
  expect(await screen.findByText(/nutrition facts not available yet/i)).toBeInTheDocument();
});
