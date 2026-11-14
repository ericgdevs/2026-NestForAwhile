import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.BASE_URL ?? "http://127.0.0.1:5173";
const isDeployed = Boolean(process.env.BASE_URL);

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "local-chromium",
      use: { ...devices["Desktop Chrome"] },
      grep: isDeployed ? /.^/ : undefined,
    },
    {
      name: "deployed-chromium",
      use: { ...devices["Desktop Chrome"] },
      grep: isDeployed ? undefined : /.^/,
    },
  ],
});
