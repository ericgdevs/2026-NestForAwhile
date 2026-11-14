import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import Signup from "./Signup";

const { signup, refresh } = vi.hoisted(() => ({
  signup: vi.fn().mockResolvedValue({ role: "Client", Client_Enrollment_Status: "Pending" }),
  refresh: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../api/client", () => ({ signup }));
vi.mock("../lib/auth", () => ({ useAuth: () => ({ refresh }) }));

test("walks account → household → finish and sends the household", async () => {
  render(<Signup />);
  fireEvent.change(screen.getByLabelText(/your name/i), { target: { value: "Synthetic Parent" } });
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "family@example.test" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "short" } });
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/at least 8/);

  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "long-enough-1" } });
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  fireEvent.change(await screen.findByLabelText("Nickname"), { target: { value: "Mom" } });
  fireEvent.click(screen.getByRole("checkbox", { name: "Type 2 diabetes" }));
  fireEvent.click(screen.getByRole("button", { name: /add a person/i }));
  fireEvent.click(screen.getAllByRole("checkbox", { name: "Nut allergy" })[1]);
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  expect(await screen.findByText(/sign in again to start shopping/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));

  await waitFor(() => expect(refresh).toHaveBeenCalled());
  expect(signup).toHaveBeenCalledWith({
    email: "family@example.test",
    password: "long-enough-1",
    name: "Synthetic Parent",
    members: [
      { nickname: "Mom", age: null, restrictions: [], allergies: [], conditions: ["E11"] },
      { nickname: undefined, age: null, restrictions: [], allergies: ["Nut Allergy"], conditions: [] },
    ],
  });
});
