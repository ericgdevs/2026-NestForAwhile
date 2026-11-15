import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Labels from "./Labels";

vi.mock("../api/client", () => ({
  getProductLabels: vi.fn().mockResolvedValue([{ sku: "SYN-OATS-001", name: "Synthetic Rolled Oats" }]),
}));

test("shows a QR code, a Code 128 barcode, the name and the SKU for each product", async () => {
  render(<Labels />);
  expect(await screen.findByRole("heading", { name: "Synthetic Rolled Oats" })).toBeInTheDocument();
  expect(screen.getByText("SYN-OATS-001")).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /QR code for SYN-OATS-001/ })).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /Code 128 barcode for SYN-OATS-001/ })).toBeInTheDocument();
});
