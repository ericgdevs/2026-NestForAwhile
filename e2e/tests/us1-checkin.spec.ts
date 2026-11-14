import { test, expect } from "../fixtures/auth";

test.describe("US1 client check-in", () => {
  test("active client can sign in", async ({ page, loginAs }) => {
    test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
    await loginAs("client");
    await expect(page.getByRole("heading", { name: /mtg warehouse/i })).toBeVisible();
  });

  test("invalid credentials show a friendly message", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("invalid@example.test");
    await page.getByLabel("Password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText(/couldn't sign you in/i)).toBeVisible();
  });

  test("non-active client sees an enrollment message", async ({ page }) => {
    test.skip(!process.env.E2E_INACTIVE_EMAIL, "Synthetic e2e credentials are not configured");
    await page.goto("/login");
    await page.getByLabel("Email").fill(process.env.E2E_INACTIVE_EMAIL!);
    await page.getByLabel("Password").fill(process.env.E2E_INACTIVE_PASSWORD ?? "demo-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText(/not active yet/i)).toBeVisible();
  });

  test("volunteer can see active shopper count", async ({ page, loginAs }) => {
    test.skip(!process.env.E2E_VOLUNTEER_EMAIL, "Synthetic e2e credentials are not configured");
    await loginAs("volunteer");
    await expect(page.getByText(/active shoppers:/i)).toBeVisible();
  });
});
