import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import BarcodeScanner from "./BarcodeScanner";

const zxing = vi.hoisted(() => ({
  decode: vi.fn(),
  stop: vi.fn(),
}));

vi.mock("@zxing/browser", () => ({
  BrowserMultiFormatReader: class {
    decodeFromConstraints = zxing.decode;
  },
}));

beforeEach(() => {
  zxing.decode.mockReset();
  zxing.stop.mockReset();
});

function tapScan() {
  fireEvent.click(screen.getByRole("button", { name: /scan with camera/i }));
}

test("permission denied shows a clear message and keeps manual entry available", async () => {
  zxing.decode.mockRejectedValue(new DOMException("denied", "NotAllowedError"));
  render(<BarcodeScanner onDetected={vi.fn()} />);
  tapScan();
  expect(await screen.findByRole("alert")).toHaveTextContent(/permission was denied/i);
  expect(screen.getByRole("button", { name: /scan with camera/i })).toBeInTheDocument();
});

test("no camera shows a clear message", async () => {
  zxing.decode.mockRejectedValue(new DOMException("none", "NotFoundError"));
  render(<BarcodeScanner onDetected={vi.fn()} />);
  tapScan();
  expect(await screen.findByRole("alert")).toHaveTextContent(/no camera was found/i);
});

test("asks for the back camera as an ideal at 1280x720, then reports one read and stops", async () => {
  const onDetected = vi.fn();
  zxing.decode.mockImplementation(async (_constraints, _video, callback) => {
    setTimeout(() => {
      callback({ getText: () => " SYN-OATS-001 " });
      callback({ getText: () => "SYN-OATS-001" }); // a second frame must not report again
    });
    return { stop: zxing.stop };
  });
  render(<BarcodeScanner onDetected={onDetected} />);
  tapScan();

  await vi.waitFor(() => expect(onDetected).toHaveBeenCalledWith("SYN-OATS-001"));
  expect(onDetected).toHaveBeenCalledTimes(1);
  expect(zxing.stop).toHaveBeenCalled();
  expect(zxing.decode.mock.calls[0][0].video).toEqual({
    facingMode: { ideal: "environment" },
    width: { ideal: 1280 },
    height: { ideal: 720 },
  });
});

test("stops the camera when leaving the page", async () => {
  zxing.decode.mockResolvedValue({ stop: zxing.stop });
  const { unmount } = render(<BarcodeScanner onDetected={vi.fn()} />);
  tapScan();
  await screen.findByRole("button", { name: /stop camera/i });
  unmount();
  expect(zxing.stop).toHaveBeenCalled();
});
