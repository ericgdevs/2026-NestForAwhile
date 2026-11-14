import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import Profile from "./Profile";

const { apiRequest, getMe } = vi.hoisted(() => ({
  apiRequest: vi.fn(),
  getMe: vi.fn(),
}));

vi.mock("../api/client", () => ({ apiRequest, getMe }));

beforeEach(() => {
  apiRequest.mockResolvedValue({});
  getMe.mockResolvedValue({ profile: { restrictions: [] } });
});

test("offers all nine choices and saves selected restrictions", async () => {
  render(<Profile />);
  expect(screen.getAllByRole("checkbox")).toHaveLength(9);
  fireEvent.click(screen.getByLabelText("Low Sodium"));
  fireEvent.click(screen.getByRole("button", { name: /save choices/i }));

  await waitFor(() =>
    expect(apiRequest).toHaveBeenCalledWith(
      "/me/profile",
      expect.objectContaining({
        method: "PUT",
        body: { restrictions: ["Low Sodium"], allergies: [], preferences: [] },
      }),
    ),
  );
  expect(screen.getByText(/choices were saved/i)).toBeInTheDocument();
});
