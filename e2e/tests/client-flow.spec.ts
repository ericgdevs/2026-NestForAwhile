import { test, expect, type Page } from "@playwright/test";

// Client shopping flow (design: docs/superpowers/specs/2026-11-14-client-flow-design.md).
// Needs the api/client-flow backend; skips cleanly until it is merged.

async function needsClientFlow(page: Page) {
  const probe = await page.request.get("/clients/pending");
  test.skip(probe.status() === 404, "api/client-flow backend is not deployed here yet");
}

async function signIn(page: Page, email: string) {
  const response = await page.request.post("/auth/login", { data: { email, password: "demo-password" } });
  expect(response.ok()).toBeTruthy();
}

test.describe("client on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("signs up a household and waits for approval with no shopping session", async ({ page }) => {
    await needsClientFlow(page);
    await page.goto("/login");
    await page.getByRole("link", { name: "Create Account" }).click();
    await page.getByLabel(/your name/i).fill("Synthetic Newcomer");
    await page.getByLabel("Email").fill(`newcomer-${Date.now()}@example.test`);
    await page.getByLabel("Password").fill("synthetic-pass-1");
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByLabel("Nickname").fill("Grandpa");
    await page.getByRole("checkbox", { name: "High blood pressure" }).click();
    await page.getByRole("button", { name: "Next" }).click();
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page.getByRole("heading", { name: "Almost ready" })).toBeVisible();
    await page.goto("/scan");
    await expect(page.getByRole("heading", { name: "Scan a product" })).toHaveCount(0);
  });

  test("scan shows who an item is not for, recipes go to the list, cart shows a QR", async ({ page }) => {
    await needsClientFlow(page);
    await signIn(page, "client.active@example.test");
    await page.goto("/scan?code=SYN-CRACK-001");
    await expect(page.getByText(/Not for/)).toContainText("Little one");

    await page.goto("/scan?code=SYN-OATS-001");
    await page.locator("button[aria-label^='Save:']").first().click();
    await expect(page.locator("button[aria-label^='Saved:']").first()).toBeVisible();

    await page.goto("/list");
    await page.getByLabel("Type or paste your list").fill("black beans");
    await page.getByRole("button", { name: "Find these items" }).click();
    await page.getByRole("button", { name: /to my list/ }).click();
    await expect(page.getByText(/Aisle .* · Shelf .* · Bin/).first()).toBeVisible();

    const oats = await (await page.request.get("/products/scan/SYN-OATS-001")).json();
    await page.request.post("/cart/items", { data: { product_id: oats.product_id, quantity: 1 } });
    await page.goto("/cart");
    await page.getByRole("button", { name: "Show at checkout" }).click();
    await expect(page.getByRole("img", { name: "Checkout QR code" })).toBeVisible();
  });
});

test("volunteer confirms an allergy item before completing checkout", async ({ page, browser }) => {
  await needsClientFlow(page);
  const client = await browser.newPage();
  await signIn(client, "client.active@example.test");
  const crackers = await (await client.request.get("/products/scan/SYN-CRACK-001")).json();
  await client.request.post("/cart/items", { data: { product_id: crackers.product_id, quantity: 1 } });
  const { client_id } = await (await client.request.get("/me/session")).json();

  await signIn(page, "volunteer@example.test");
  await page.goto("/checkout");
  await page.getByLabel("Client ID").fill(String(client_id));
  await page.getByRole("button", { name: "Load cart" }).click();
  await expect(page.getByRole("button", { name: "Complete checkout" })).toBeDisabled();
  await page.getByRole("button", { name: "Confirmed with client" }).click();
  await page.getByRole("button", { name: "Complete checkout" }).click();
  await expect(page.getByText(/Receipt #/)).toBeVisible();
});

test("manager sees pending accounts with names and approves one", async ({ page }) => {
  await needsClientFlow(page);
  await signIn(page, "warehouse.manager@example.test");
  await page.goto("/approvals");
  const approve = page.getByRole("button", { name: /Approve #/ }).first();
  await expect(approve).toBeVisible();
  await approve.click();
  await expect(page.getByRole("status")).toContainText("Approved 1");
});
