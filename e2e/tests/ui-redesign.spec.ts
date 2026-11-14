import { test, expect, type Page } from "@playwright/test";

// Signs in through the page's own request context so the session cookie reaches the page.
async function signIn(page: Page, role: "CLIENT" | "VOLUNTEER") {
  const email = process.env[`E2E_${role}_EMAIL`];
  const password = process.env[`E2E_${role}_PASSWORD`];
  test.skip(!email || !password, "Synthetic e2e credentials are not configured");
  const response = await page.request.post("/auth/login", { data: { email, password } });
  expect(response.ok()).toBeTruthy();
  await page.goto("/");
}

test("volunteer navigation lists only the screens a volunteer can open", async ({ page }) => {
  await signIn(page, "VOLUNTEER");
  const nav = page.getByRole("navigation", { name: "Primary navigation" });
  await expect(nav.getByRole("link")).toHaveText(["Overview", "Checkout"]);
});

test.describe("client on a phone", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("uses the bottom tab bar with a List tab and Household in the top bar", async ({ page }) => {
    await signIn(page, "CLIENT");
    const tabs = page.getByRole("navigation", { name: "Mobile navigation" });
    await expect(tabs).toBeVisible();
    await expect(tabs.getByRole("link")).toHaveText(["Home", "Scan", "List", "Cart", "Recipes"]);
    await expect(page.getByRole("link", { name: "Household" })).toHaveAttribute("href", "/profile");

    // Clients are identified by role and household, never by name.
    await expect(page.getByText("Active Client")).toHaveCount(0);
  });
});
