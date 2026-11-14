import { test, expect } from "../fixtures/auth";

test("client cannot open volunteer checkout", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("client");
  await page.goto("/checkout");
  await expect(page.getByRole("heading", { name: "Unauthorized" })).toBeVisible();
});
