import { test, expect } from "../fixtures/auth";

test.describe("US4 barcode safety scan", () => {
  test("manual SKU shows a product result", async ({ page, loginAs }) => {
    test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
    await loginAs("client");
    await page.goto("/scan");
    await page.getByLabel("SKU or barcode").fill("SYN-OATS-001");
    await page.getByRole("button", { name: "Check" }).click();
    await expect(page.getByRole("heading", { name: /synthetic rolled oats/i })).toBeVisible();
    await expect(page.getByRole("status")).toBeVisible();
  });

  test("unknown SKU shows a friendly error", async ({ page, loginAs }) => {
    test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
    await loginAs("client");
    await page.goto("/scan");
    await page.getByLabel("SKU or barcode").fill("unknown-synthetic-sku");
    await page.getByRole("button", { name: "Check" }).click();
    await expect(page.getByText(/couldn't find that product/i)).toBeVisible();
  });

  test("camera scanner is present for permission smoke testing", async ({ page, loginAs }) => {
    test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
    await loginAs("client");
    await page.goto("/scan");
    await expect(page.getByRole("button", { name: /scan with camera/i })).toBeVisible();
  });
});
