import { test, expect } from "../fixtures/auth";

test("client sees safe recommendations with rationale and quantities", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("client");
  await expect(page.getByRole("heading", { name: /recommended for you/i })).toBeVisible();
  await expect(page.getByText(/suggested quantity:/i).first()).toBeVisible();
  await expect(page.locator("article").first()).toContainText(/matches|guideline|confirm/i);
  await expect(page.getByText("Not recommended")).toHaveCount(0);
});
