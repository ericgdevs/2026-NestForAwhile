import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import CheckoutQr from "./CheckoutQr";

vi.mock("../api/client", () => ({
  getMySession: vi.fn().mockResolvedValue({ Shopping_Session_Token: "synthetic-token", client_id: 17 }),
}));

test("draws a QR of the session token and shows the client ID", async () => {
  render(<CheckoutQr />);
  const qr = await screen.findByRole("img", { name: "Checkout QR code" });
  expect(qr.querySelector("path")?.getAttribute("d")).toMatch(/^M\d+ \d+h1v1h-1z/);
  expect(screen.getByText("17")).toBeInTheDocument();
});
