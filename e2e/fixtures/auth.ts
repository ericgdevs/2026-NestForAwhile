import { test as base, expect } from "@playwright/test";

export const roles = [
  "client",
  "volunteer",
  "warehouse_staff",
  "warehouse_manager",
  "director",
] as const;

export type TestRole = (typeof roles)[number];

const defaultCredentials: Record<TestRole, { email: string; password: string }> = {
  client: { email: "client.active@example.test", password: "demo-password" },
  volunteer: { email: "volunteer@example.test", password: "demo-password" },
  warehouse_staff: { email: "warehouse.staff@example.test", password: "demo-password" },
  warehouse_manager: { email: "warehouse.manager@example.test", password: "demo-password" },
  director: { email: "director@example.test", password: "demo-password" },
};

type AuthFixture = {
  loginAs: (role: TestRole) => Promise<void>;
};

export const test = base.extend<AuthFixture>({
  loginAs: async ({ page }, use) => {
    await use(async (role) => {
      const prefix = `E2E_${role.toUpperCase()}_`;
      const fallback = defaultCredentials[role];
      const email = process.env[`${prefix}EMAIL`] ?? fallback?.email;
      const password = process.env[`${prefix}PASSWORD`] ?? fallback?.password;
      if (!email || !password) {
        throw new Error(`Missing ${prefix}EMAIL or ${prefix}PASSWORD for e2e login`);
      }

      const response = await page.request.post("/auth/login", {
        data: { email, password },
      });
      expect(response.ok()).toBeTruthy();
      await page.goto("/");
    });
  },
});

export { expect };
