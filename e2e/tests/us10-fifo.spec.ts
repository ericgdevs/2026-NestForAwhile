import { test, expect } from "../fixtures/auth";

test("warehouse staff can view FIFO lots", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_WAREHOUSE_STAFF_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("warehouse_staff");
  await page.goto("/lots");
  await expect(page.getByRole("heading", { name: "FIFO lots" })).toBeVisible();
});
