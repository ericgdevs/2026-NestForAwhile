import { test, expect } from "../fixtures/auth";

test("client queue screen is available", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("client");
  await page.goto("/waiting");
  await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
});
