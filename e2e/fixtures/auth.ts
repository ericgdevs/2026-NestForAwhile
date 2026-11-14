import { test as base, expect } from "@playwright/test";

export const roles = [
  "client",
  "volunteer",
  "warehouse_staff",
  "warehouse_manager",
  "director",
] as const;

export type TestRole = (typeof roles)[number];

type AuthFixture = {
  loginAs: (role: TestRole) => Promise<void>;
};

export const test = base.extend<AuthFixture>({
  loginAs: async ({ page, request }, use) => {
    await use(async (role) => {
      const prefix = `E2E_${role.toUpperCase()}_`;
      const email = process.env[`${prefix}EMAIL`];
      const password = process.env[`${prefix}PASSWORD`];
      if (!email || !password) {
        throw new Error(`Missing ${prefix}EMAIL or ${prefix}PASSWORD for e2e login`);
      }

      const response = await request.post("/auth/login", {
        data: { email, password },
      });
      expect(response.ok()).toBeTruthy();
      await page.goto("/");
    });
  },
});

export { expect };
