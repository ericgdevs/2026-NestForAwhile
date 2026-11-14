import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { StatusBadge } from "./StatusBadge";

test.each([
  ["Approved", "Good match"],
  ["Capped", "Please check"],
  ["Restricted", "Not recommended"],
] as const)("shows text and an icon for %s", (status, label) => {
  render(<StatusBadge status={status} />);

  expect(screen.getByRole("status", { name: new RegExp(label) })).toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent(label);
});
