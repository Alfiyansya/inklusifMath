/**
 * E2E: Homepage (/) — public landing page.
 *
 * Tests:
 *   - Page loads with correct title
 *   - Skip link exists and is keyboard-accessible (a11y)
 *   - Main heading visible
 *   - Login and Register links present
 *   - No broken external resources (minimal)
 */

import { test, expect } from "@playwright/test";

test.describe("Homepage /", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("has correct page title", async ({ page }) => {
    await expect(page).toHaveTitle(/InklusifMath/i);
  });

  test("has skip-to-content link as first focusable element", async ({ page }) => {
    // Tab once from top — first focusable should be skip link
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus");
    // Skip link text contains 'konten' or 'content' or 'Skip'
    await expect(focused).toContainText(/konten|content|skip/i);
  });

  test("has main heading visible", async ({ page }) => {
    // At least one h1 should be present
    await expect(page.locator("h1").first()).toBeVisible();
  });

  test("has Login link", async ({ page }) => {
    const loginLink = page.getByRole("link", { name: /masuk|login/i });
    await expect(loginLink).toBeVisible();
  });

  test("has Register link", async ({ page }) => {
    const registerLink = page.getByRole("link", { name: /daftar|register/i });
    await expect(registerLink).toBeVisible();
  });

  test("login link navigates to /login", async ({ page }) => {
    const loginLink = page.getByRole("link", { name: /masuk|login/i }).first();
    await loginLink.click();
    await expect(page).toHaveURL(/\/login/);
  });
});
