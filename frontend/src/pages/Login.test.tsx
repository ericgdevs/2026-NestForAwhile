import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import Login from "./Login";

const signIn = vi.fn();

vi.mock("../lib/auth", () => ({
  useAuth: () => ({ signIn }),
}));

beforeEach(() => {
  signIn.mockReset();
});

test("submits credentials and navigates after signing in", async () => {
  render(<Login />);
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "client@example.test" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  await waitFor(() => expect(signIn).toHaveBeenCalledWith("client@example.test", "secret"));
});

test("shows friendly messages for invalid and inactive accounts", async () => {
  signIn.mockRejectedValueOnce(new Error("Invalid credentials"));
  render(<Login />);
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "x@example.test" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "bad" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByText(/couldn't sign you in/i)).toBeInTheDocument();

  signIn.mockRejectedValueOnce(new Error("Client enrollment is not Active"));
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByText(/not active yet/i)).toBeInTheDocument();
});

test("explains how to create an account", () => {
  render(<Login />);
  fireEvent.click(screen.getByRole("button", { name: "Create Account" }));
  expect(screen.getByText(/ask staff to create your account/i)).toBeInTheDocument();
});
