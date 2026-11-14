import { test, expect } from "../fixtures/auth";

test("client can add, change, remove, and reload a cart item", async ({ page, loginAs }) => {
  test.skip(!process.env.E2E_CLIENT_EMAIL, "Synthetic e2e credentials are not configured");
  await loginAs("client");
  await page.goto("/scan");
  await page.getByLabel("SKU or barcode").fill("SYN-OATS-001");
  await page.getByRole("button", { name: "Check" }).click();
  await page.getByRole("button", { name: "Add to cart" }).click();
  await page.goto("/cart");
  await expect(page.getByText("Synthetic Rolled Oats")).toBeVisible();
  await page.getByRole("button", { name: /increase synthetic rolled oats/i }).click();
  await expect(page.getByText("2")).toBeVisible();
  await page.getByRole("button", { name: /decrease synthetic rolled oats/i }).click();
  await page.getByRole("button", { name: /decrease synthetic rolled oats/i }).click();
  await expect(page.getByText("Your cart is empty.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Your cart is empty.")).toBeVisible();
});
