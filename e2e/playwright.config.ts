import { defineConfig, devices } from "@playwright/test";

const deployedBaseURL = process.env.DEPLOYED_BASE_URL;
const baseURL = deployedBaseURL || process.env.BASE_URL || "http://127.0.0.1:8000";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: deployedBaseURL
    ? undefined
    : {
        command:
          'bash -c "cd ../backend && export JWT_SECRET=synthetic-e2e-secret SEED_DEMO_DATA=true DATABASE_URL=sqlite:///./e2e.db FIELD_ENCRYPTION_KEY=\\$(python3 -c \\"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\\") && alembic upgrade head && python3 -m seed.load && uvicorn vercel_app:app --host 127.0.0.1 --port 8000"',
        url: "http://127.0.0.1:8000/health",
        reuseExistingServer: true,
        timeout: 60_000,
      },
});
