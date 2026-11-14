import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import BarcodeScanner from "./BarcodeScanner";

vi.mock("@zxing/browser", () => ({
  BrowserMultiFormatReader: class {
    decodeFromConstraints = vi.fn().mockRejectedValue(new Error("No camera"));
  },
}));

test("offers camera scanning and a friendly fallback", async () => {
  render(<BarcodeScanner onDetected={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: /scan with camera/i }));
  expect(await screen.findByText(/camera access is unavailable/i)).toBeInTheDocument();
});
