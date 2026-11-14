import { expect, test } from "vitest";

import { canVisit, navFor } from "./roles";

test.each([
  ["Client", ["/", "/scan", "/cart", "/recipes", "/profile"]],
  ["Volunteer", ["/", "/checkout"]],
  ["Warehouse Staff", ["/", "/audit", "/replenishment", "/lots"]],
  ["Warehouse Manager", ["/", "/checkout", "/audit", "/replenishment", "/lots", "/analytics", "/reports"]],
  ["Director", ["/", "/analytics", "/reports"]],
] as const)("%s nav shows only screens the role can open", (role, hrefs) => {
  const links = navFor(role);
  expect(links.map((link) => link.href)).toEqual(hrefs);
  expect(links.every((link) => canVisit(role, link.href))).toBe(true);
});
