import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import App from "../App";
import { getMe, login } from "../api/client";

vi.mock("../api/client", () => ({
  getMe: vi.fn(),
  getAnalytics: vi.fn().mockResolvedValue({ waste_reduction: { expiring_soon_lots: 0 } }),
  getCapacity: vi.fn().mockResolvedValue({ Active_Floor_Shoppers: 0 }),
  getInventoryLots: vi.fn().mockResolvedValue([]),
  getReplenishment: vi.fn().mockResolvedValue([]),
  getPendingClients: vi.fn().mockResolvedValue([]),
  getRecommendations: vi.fn().mockResolvedValue([]),
  getVisit: vi.fn().mockResolvedValue({ status: "shopping", Shopping_Session_Token: "tok" }),
  getShoppingList: vi.fn().mockResolvedValue({ items: [] }),
  getHousehold: vi.fn().mockResolvedValue({ members: [] }),
  login: vi.fn(),
  apiRequest: vi.fn().mockResolvedValue(undefined),
}));

beforeEach(() => {
  window.history.replaceState({}, "", "/");
  vi.mocked(login).mockResolvedValue({ role: "Client" });
});

test("a first visit signs in as the demo customer without a login form", async () => {
  vi.mocked(getMe).mockRejectedValueOnce(new Error("not signed in")).mockResolvedValue({
    Household_Size: 2,
    Client_Enrollment_Status: "Active",
    profile: { restrictions: [], allergies: [], preferences: [] },
  });
  render(<App />);

  await waitFor(() => expect(login).toHaveBeenCalledWith(expect.objectContaining({ email: "client.active@example.test" })));
  expect(screen.queryByRole("heading", { name: "Sign in" })).not.toBeInTheDocument();
});

test("the demo role dropdown signs in as the chosen role", async () => {
  vi.mocked(getMe).mockResolvedValue({ role: "Client", Household_Size: 2, Client_Enrollment_Status: "Active", profile: { restrictions: [], allergies: [], preferences: [] } });
  render(<App />);
  vi.mocked(login).mockResolvedValue({ role: "Director" });

  fireEvent.change((await screen.findAllByLabelText("Demo role"))[0], { target: { value: "Director" } });

  await waitFor(() => expect(login).toHaveBeenCalledWith(expect.objectContaining({ email: "director@example.test" })));
});
