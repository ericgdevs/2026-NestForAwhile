import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Approvals from "./Approvals";

const { getPendingClients, approveClient } = vi.hoisted(() => ({
  getPendingClients: vi.fn().mockResolvedValue([
    { client_id: 7, name: "Synthetic Pending", Household_Size: 3, created_at: "2026-11-14T10:00:00" },
  ]),
  approveClient: vi.fn().mockResolvedValue({}),
}));

vi.mock("../api/client", () => ({ getPendingClients, approveClient }));

test("lists pending accounts with names and approves one", async () => {
  render(<Approvals />);
  expect(await screen.findByText("Synthetic Pending")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Approve #7" }));
  await waitFor(() => expect(approveClient).toHaveBeenCalledWith(7));
  expect(await screen.findByText(/no accounts are waiting/i)).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent("Approved 1 account");
});
