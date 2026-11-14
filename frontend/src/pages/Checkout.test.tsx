import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Checkout from "./Checkout";

const { validateCheckout, completeCheckout } = vi.hoisted(() => ({
  validateCheckout: vi.fn().mockResolvedValue({ valid: false, errors: ["Product is restricted."] }),
  completeCheckout: vi.fn(),
}));

vi.mock("../api/client", () => ({ validateCheckout, completeCheckout }));

test("shows hard-stop checkout validation errors", async () => {
  render(<Checkout />);
  fireEvent.change(screen.getByLabelText("Shopping session token"), { target: { value: "token" } });
  fireEvent.click(screen.getByRole("button", { name: "Review cart" }));
  await waitFor(() => expect(screen.getByText(/checkout needs attention/i)).toBeInTheDocument());
});

test("explains a token that has no active session", async () => {
  validateCheckout.mockRejectedValueOnce(new Error("Active shopping session not found"));
  render(<Checkout />);
  fireEvent.change(screen.getByLabelText("Shopping session token"), { target: { value: "bad" } });
  fireEvent.click(screen.getByRole("button", { name: "Review cart" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/session not found/i);
});
