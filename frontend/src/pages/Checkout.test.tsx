import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import Checkout from "./Checkout";

const api = vi.hoisted(() => ({
  lookupCheckout: vi.fn(),
  acknowledgeAllergy: vi.fn(),
  addCheckoutItem: vi.fn(),
  removeCheckoutItem: vi.fn(),
  overrideItem: vi.fn(),
  completeCheckout: vi.fn().mockResolvedValue({ checkout_id: 42, total_lb: 3.5 }),
}));
const role = vi.hoisted(() => ({ current: "Volunteer" }));

vi.mock("../api/client", () => api);
vi.mock("../lib/auth", () => ({ useAuth: () => ({ user: { role: role.current } }) }));
vi.mock("../components/BarcodeScanner", () => ({ default: () => <div>Camera scanner</div> }));

const crackers = {
  product_id: 4,
  name: "Synthetic Nut Crackers",
  quantity: 1,
  status: "Capped",
  not_for: [{ nickname: "Little one", reason: "Nut Allergy" }],
  allergy_match: true,
  acknowledged: false,
  overridden: false,
};
const review = {
  Shopping_Session_Token: "tok",
  client_id: 1,
  Client_Enrollment_Status: "Active",
  items: [crackers],
  blocking: [],
  needs_ack: [{ product_id: 4, name: crackers.name, not_for: crackers.not_for }],
};

beforeEach(() => {
  role.current = "Volunteer";
});

async function loadById() {
  render(<Checkout />);
  fireEvent.change(screen.getByLabelText("Client ID"), { target: { value: "1" } });
  fireEvent.click(screen.getByRole("button", { name: "Load cart" }));
  await screen.findByRole("region", { name: "Cart to confirm" });
}

test("allergy item pauses checkout until the volunteer confirms it", async () => {
  api.lookupCheckout.mockResolvedValue(review);
  api.acknowledgeAllergy.mockResolvedValue({ ...review, needs_ack: [], items: [{ ...crackers, acknowledged: true }] });
  await loadById();

  expect(api.lookupCheckout).toHaveBeenCalledWith({ client_id: 1 });
  expect(screen.getByText(/checkout needs attention/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Complete checkout" })).toBeDisabled();

  fireEvent.click(screen.getByRole("button", { name: "Confirmed with client" }));
  await waitFor(() => expect(api.acknowledgeAllergy).toHaveBeenCalledWith("tok", 4));
  fireEvent.click(await screen.findByRole("button", { name: "Complete checkout" }));
  expect(await screen.findByText("Receipt #42")).toBeInTheDocument();
});

test("Red items block; only managers see the override", async () => {
  const red = { ...review, needs_ack: [], blocking: ["Synthetic Nut Crackers isn't safe for anyone in this household."], items: [{ ...crackers, status: "Restricted" }] };
  api.lookupCheckout.mockResolvedValue(red);
  await loadById();
  expect(screen.queryByRole("button", { name: "Manager override" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Complete checkout" })).toBeDisabled();
});

test("volunteer adds a missed item and removes one", async () => {
  api.lookupCheckout.mockResolvedValue({ ...review, needs_ack: [] });
  api.addCheckoutItem.mockResolvedValue(review);
  api.removeCheckoutItem.mockResolvedValue({ ...review, items: [] });
  await loadById();

  fireEvent.change(screen.getByLabelText(/missed an item/i), { target: { value: "000000000002" } });
  fireEvent.click(screen.getByRole("button", { name: "Add item" }));
  await waitFor(() => expect(api.addCheckoutItem).toHaveBeenCalledWith("tok", "000000000002"));
  fireEvent.click(screen.getByRole("button", { name: "Remove Synthetic Nut Crackers" }));
  await waitFor(() => expect(api.removeCheckoutItem).toHaveBeenCalledWith("tok", 4));
});

test("explains a client with no active visit", async () => {
  api.lookupCheckout.mockRejectedValue(new Error("Active shopping session not found"));
  render(<Checkout />);
  fireEvent.change(screen.getByLabelText("Client ID"), { target: { value: "9" } });
  fireEvent.click(screen.getByRole("button", { name: "Load cart" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/session not found/i);
});
