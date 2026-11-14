import { test, expect } from "../fixtures/auth";

test("client can save dietary choices and see them after signing in again", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("client");
  await page.goto("/profile");
  await page.getByLabel("Vegetarian").check();
  await page.getByRole("button", { name: /save choices/i }).click();
  await expect(page.getByText(/choices were saved/i)).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Vegetarian")).toBeChecked();
});
