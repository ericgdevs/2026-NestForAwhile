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
