import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Scan from "./Scan";

vi.mock("../components/BarcodeScanner", () => ({
  default: () => <div>Camera scanner</div>,
}));
vi.mock("../api/client", () => ({
  scanProduct: vi.fn().mockResolvedValue({
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
  }),
  saveCartItem: vi.fn(),
}));

test("supports manual SKU lookup and renders the result card", async () => {
  render(<Scan />);
  fireEvent.change(screen.getByLabelText("SKU or barcode"), {
    target: { value: "SYN-OATS-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Check" }));
  await waitFor(() => expect(screen.getByRole("heading", { name: "Synthetic Oats" })).toBeInTheDocument());
  expect(screen.getByText(/matches the selected dietary profile/i)).toBeInTheDocument();
});
