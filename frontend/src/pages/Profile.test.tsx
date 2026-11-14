import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import Profile from "./Profile";

const { getHousehold, saveHousehold } = vi.hoisted(() => ({
  getHousehold: vi.fn(),
  saveHousehold: vi.fn(),
}));

vi.mock("../api/client", () => ({ getHousehold, saveHousehold }));

const household = {
  members: [
    { nickname: "Person 1", age: 38, restrictions: ["Low Sodium"], allergies: [] },
    { nickname: "Little one", age: 7, restrictions: [], allergies: ["Nut Allergy"] },
  ],
};

beforeEach(() => {
  getHousehold.mockResolvedValue(household);
  saveHousehold.mockImplementation(async (members) => ({
    members: members.map((m: { nickname?: string }, i: number) => ({ ...household.members[i], ...m })),
  }));
});

test("edits each person and saves the whole household", async () => {
  render(<Profile />);
  const child = await screen.findByRole("region", { name: "Little one" });
  expect(screen.getAllByRole("checkbox", { name: "Low Sodium" })[0]).toBeChecked();

  fireEvent.change(screen.getAllByLabelText("Nickname")[0], { target: { value: "Mom" } });
  fireEvent.click(child.querySelectorAll('input[type="checkbox"]')[0]); // Little one: Low Sugar
  fireEvent.click(screen.getByRole("button", { name: /save choices/i }));

  await waitFor(() => expect(saveHousehold).toHaveBeenCalled());
  const [sent] = saveHousehold.mock.calls[0];
  expect(sent[0]).toMatchObject({ nickname: "Mom", age: 38, restrictions: ["Low Sodium"] });
  expect(sent[1]).toMatchObject({ nickname: "Little one", restrictions: ["Low Sugar"], allergies: ["Nut Allergy"] });
  expect(await screen.findByText(/choices were saved/i)).toBeInTheDocument();
});

test("adds a person", async () => {
  render(<Profile />);
  await screen.findByRole("region", { name: "Little one" });
  fireEvent.click(screen.getByRole("button", { name: /add a person/i }));
  expect(screen.getAllByLabelText("Nickname")).toHaveLength(3);
});
