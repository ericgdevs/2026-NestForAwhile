import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import NotForLine from "./NotForLine";

test("names who an item is not for and flags allergies", () => {
  const { container } = render(
    <NotForLine allergy notFor={[{ nickname: "Little one", reason: "Nut Allergy" }]} />,
  );
  expect(container.firstChild).toHaveTextContent("Not for Little one: Nut Allergy (allergy)");
  expect(screen.getByText("Little one").tagName).toBe("STRONG");
});

test("renders nothing when everyone can have it", () => {
  const { container } = render(<NotForLine notFor={[]} />);
  expect(container).toBeEmptyDOMElement();
});
