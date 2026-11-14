import { test, expect } from "../fixtures/auth";

test("volunteer checkout page supports session review", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_VOLUNTEER_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("volunteer");
  await page.goto("/checkout");
  await page.getByLabel("Shopping session token").fill("synthetic-session-token");
  await page.getByRole("button", { name: "Review cart" }).click();
  await expect(page.getByRole("heading", { name: "Checkout" })).toBeVisible();
});
