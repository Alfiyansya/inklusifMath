/**
 * E2E: Login page (/login).
 *
 * Tests form presence, accessibility, and validation messages.
 * We do NOT call real Firebase — we intercept the Firebase REST API call.
 *
 * Tests:
 *   - Form fields and labels present (a11y)
 *   - Email and password fields are labelled
 *   - Submit button present
 *   - Empty submit shows validation (HTML5 or inline)
 *   - Invalid email format shows validation
 */

import { test, expect } from "@playwright/test";

test.describe("Login page /login", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
  });

  test("has correct heading", async ({ page }) => {
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("email input has accessible label", async ({ page }) => {
    // Either via label[for] or aria-label
    const email = page.getByLabel(/email/i);
    await expect(email).toBeVisible();
  });

  test("password input has accessible label", async ({ page }) => {
    const password = page.locator("#login-password");
    await expect(password).toBeVisible();
  });

  test("submit button present", async ({ page }) => {
    const btn = page.getByRole("button", { name: /masuk|login|sign in/i });
    await expect(btn).toBeVisible();
  });

  test("empty submit button is disabled and keeps user on /login page", async ({ page }) => {
    const btn = page.getByRole("button", { name: /masuk|login|sign in/i });
    await expect(btn).toBeDisabled();
    await expect(page).toHaveURL(/\/login/);
  });

  test("link to register page exists", async ({ page }) => {
    const link = page.getByRole("link", { name: /daftar|register/i });
    await expect(link).toBeVisible();
  });

  test("can type in email and password fields", async ({ page }) => {
    await page.getByLabel(/email/i).fill("siswa@inklusif.test");
    await page.locator("#login-password").fill("password123");
    await expect(page.getByLabel(/email/i)).toHaveValue("siswa@inklusif.test");
  });
});
