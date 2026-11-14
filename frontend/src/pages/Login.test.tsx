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

test("links to self sign-up", () => {
  render(<Login />);
  expect(screen.getByRole("link", { name: "Create Account" })).toHaveAttribute("href", "/signup");
});

test("toggles password visibility", () => {
  render(<Login />);
  const password = screen.getByLabelText("Password");
  const toggle = screen.getByRole("button", { name: "Show password" });

  expect(password).toHaveAttribute("type", "password");
  fireEvent.click(toggle);
  expect(password).toHaveAttribute("type", "text");
  expect(screen.getByRole("button", { name: "Hide password" })).toBeInTheDocument();
});
