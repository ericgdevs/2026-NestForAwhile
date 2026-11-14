import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import App from "../App";
import { getMe, getVisit } from "../api/client";

vi.mock("../api/client", () => ({ getMe: vi.fn(), getVisit: vi.fn(), login: vi.fn(), apiRequest: vi.fn() }));

beforeEach(() => {
  vi.mocked(getMe).mockResolvedValue({ role: "Client", client_id: 5, Client_Enrollment_Status: "Pending", members: [] });
  vi.mocked(getVisit).mockResolvedValue({ status: "awaiting_approval" });
});

test("a Pending client sees the awaiting-approval screen instead of shopping", async () => {
  window.history.replaceState({}, "", "/scan");
  render(<App />);
  await waitFor(() => expect(screen.getByRole("heading", { name: "Almost ready" })).toBeInTheDocument());
  expect(screen.queryByRole("heading", { name: "Scan a product" })).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: /review your household/i })).toHaveAttribute("href", "/profile");
});
