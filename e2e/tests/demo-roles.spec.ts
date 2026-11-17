import { test, expect, type Page } from "@playwright/test";

// Demo mode: no login form. A first visit is the customer view; the nav dropdown switches roles.
test.use({ viewport: { width: 1440, height: 900 } });

const roleSelect = (page: Page) => page.getByLabel("Demo role").first();

async function switchTo(page: Page, role: string) {
  await roleSelect(page).selectOption(role);
  await expect(roleSelect(page)).toHaveValue(role);
}

test("first visit lands on the customer view with no login form", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Epic-Cure Food System" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sign in" })).toHaveCount(0);
  await expect(roleSelect(page)).toHaveValue("Client");
  await expect(page.getByText("Change Roles Here")).toBeVisible();
});

test("the dropdown switches between every demo role and each sees its own screens", async ({ page }) => {
  await page.goto("/");
  await expect(roleSelect(page)).toHaveValue("Client");
  const nav = page.getByRole("navigation", { name: "Primary navigation" });

  await switchTo(page, "Volunteer");
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Checkout" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Analytics" })).toHaveCount(0);

  await switchTo(page, "Director");
  await expect(nav.getByRole("link", { name: "Analytics" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Checkout" })).toHaveCount(0);

  await switchTo(page, "Warehouse Manager");
  for (const name of ["Checkout", "Audit", "Restock", "Lots", "Labels", "Approvals", "Analytics"]) {
    await expect(nav.getByRole("link", { name })).toBeVisible();
  }

  await switchTo(page, "Client");
  await expect(page.getByRole("heading", { name: "Epic-Cure Food System" })).toBeVisible();
});

test("every screen for every role loads without page errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 500) errors.push(`${response.status()} ${response.url()}`);
  });
  const screens: Record<string, [string, string][]> = {
    Client: [["/scan", "Scan a product"], ["/list", "Shopping list"], ["/cart", "Your cart"], ["/recipes", "Recipes"], ["/profile", "Your household"]],
    Volunteer: [["/checkout", "Checkout"]],
    "Warehouse Manager": [["/audit", "Inventory audit"], ["/replenishment", "Restock"], ["/lots", "Lots, oldest first"], ["/labels", "Product labels"], ["/approvals", "Approvals"], ["/analytics", "Analytics"]],
    Director: [["/analytics", "Analytics"]],
  };
  await page.goto("/");
  for (const [role, pages] of Object.entries(screens)) {
    await switchTo(page, role);
    for (const [path, heading] of pages) {
      await page.goto(path);
      await expect(page.getByRole("heading", { name: heading, exact: true }).first()).toBeVisible();
    }
  }
  expect(errors).toEqual([]);
});

test("customer scans a product, adds it to the cart, and changes the quantity", async ({ page }) => {
  await page.goto("/scan");
  await page.getByPlaceholder("e.g. SYN-OATS-001").fill("SYN-OATS-001");
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByRole("heading", { name: "Synthetic Rolled Oats", exact: true })).toBeVisible();
  const added = page.waitForResponse((r) => r.url().includes("/cart/items") && r.request().method() === "POST");
  await page.getByRole("button", { name: /add to cart/i }).first().click();
  expect((await added).ok()).toBeTruthy(); // navigating away mid-request would drop the add

  await page.goto("/cart");
  await expect(page.getByRole("button", { name: "Increase Synthetic Rolled Oats" })).toBeVisible();
  const quantity = page.locator("article", { hasText: "Synthetic Rolled Oats" }).locator("output");
  const before = Number(await quantity.textContent()); // the demo cart may already hold some
  await page.getByRole("button", { name: "Increase Synthetic Rolled Oats" }).click();
  await expect(quantity).toHaveText(String(before + 1));
  for (let left = before + 1; left > 1; left--) {
    await page.getByRole("button", { name: "Decrease Synthetic Rolled Oats" }).click();
    await expect(quantity).toHaveText(String(left - 1));
  }
  await page.getByRole("button", { name: "Decrease Synthetic Rolled Oats" }).click(); // last one removes it
  await expect(page.getByText("Your cart is empty.")).toBeVisible();
});

test("an unknown SKU shows a friendly message", async ({ page }) => {
  await page.goto("/scan");
  await page.getByPlaceholder("e.g. SYN-OATS-001").fill("NOT-A-REAL-SKU");
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.getByText(/couldn't find|not found|no product/i).first()).toBeVisible();
});

test("the customer sees recommended labels and never a queue screen", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("region", { name: "Recommended groceries" }).locator(".label-panel").first()).toBeVisible();
  await expect(page.getByText(/waiting|in line|queue/i)).toHaveCount(0);
});

test("dashboard figures count up and settle on a number", async ({ page }) => {
  await page.goto("/");
  await switchTo(page, "Director");
  await page.goto("/analytics");
  const first = page.locator(".stat-card dd").first();
  await expect(first).toHaveText(/^\d[\d,.]*$/);
  await page.waitForTimeout(1200); // past the 900ms count-up
  await expect(first).toHaveText(/^\d[\d,.]*$/);
  await expect(page.locator(".stat-card").first()).toHaveCSS("box-shadow", /rgba/);
});
