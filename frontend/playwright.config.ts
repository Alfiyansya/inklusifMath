import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration for InklusifMath.
 *
 * Strategy:
 *   - Tests run against a real dev server (Next.js on port 3000)
 *   - Backend is expected on port 8000 (docker-compose or local)
 *   - We mock API responses at the network layer using route() to avoid
 *     requiring a live database for E2E tests.
 *
 * Accessibility assertions use axe-core via @axe-core/playwright.
 *
 * Run:  npm run test:e2e
 * UI:   npm run test:e2e:ui
 */

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["list"],
  ],

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    // Accessibility: run in large viewport matching typical screen reader usage
    viewport: { width: 1280, height: 720 },
    // Simulate slow network to catch loading state issues
    // launchOptions: { slowMo: 50 },
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
  ],

  // Start dev server before tests (only in local; CI uses separate step)
  webServer: process.env.CI
    ? undefined
    : {
        command: "npm run dev",
        url: "http://localhost:3000",
        reuseExistingServer: true,
        timeout: 60_000,
      },
});
