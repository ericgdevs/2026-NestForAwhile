import { test, expect } from "../fixtures/auth";

test("manager can open anonymized analytics", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_WAREHOUSE_MANAGER_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("warehouse_manager");
  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: "Analytics" })).toBeVisible();
});
