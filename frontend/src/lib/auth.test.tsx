import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import App from "../App";
import { getMe } from "../api/client";

vi.mock("../api/client", () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  apiRequest: vi.fn(),
}));

beforeEach(() => {
  window.history.replaceState({}, "", "/");
  vi.mocked(getMe).mockRejectedValue(new Error("not signed in"));
});

test("protected routes do not show private content when signed out", async () => {
  render(<App />);

  await waitFor(() => expect(screen.getByText(/please sign in/i)).toBeInTheDocument());
  expect(screen.queryByText(/welcome to the grocery/i)).not.toBeInTheDocument();
});
