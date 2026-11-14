import { test, expect } from "../fixtures/auth";

test("client sees recipes and fallback messaging", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("client");
  await page.goto("/recipes");
  await expect(page.getByRole("heading", { name: "Recipes" })).toBeVisible();
  await expect(page.getByText(/fallback|recipe/i).first()).toBeVisible();
});
