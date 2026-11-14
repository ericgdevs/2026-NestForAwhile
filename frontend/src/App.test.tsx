import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, vi } from "vitest";

import App from "./App";
import { getMe, getRecommendations } from "./api/client";

vi.mock("./api/client", () => ({
  getMe: vi.fn(),
  getRecommendations: vi.fn(),
  login: vi.fn(),
  apiRequest: vi.fn(),
}));

beforeEach(() => {
  vi.mocked(getMe).mockResolvedValue({
    name: "Synthetic Client",
    Household_Size: 2,
    Client_Enrollment_Status: "Active",
    profile: { restrictions: [], allergies: [], preferences: [] },
  });
  vi.mocked(getRecommendations).mockResolvedValue([]);
});

test("renders the warehouse shell", async () => {
  render(<App />);
  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /mtg warehouse/i })).toBeInTheDocument();
  });
});
