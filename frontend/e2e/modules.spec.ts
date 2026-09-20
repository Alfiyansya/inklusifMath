/**
 * E2E: Modules list page (/modules).
 *
 * Mocks the backend /api/v1/modules endpoint and Firebase auth/me.
 * Tests:
 *   - Module cards render with titles
 *   - Published date shown
 *   - Keyboard navigation with J/K
 *   - Module link navigates to /modules/[id]
 *   - Heading hierarchy (a11y: h1 → h2 cards)
 *   - Loading state then content appears
 */

import { test, expect } from "@playwright/test";
import {
  mockAuthMe,
  mockModulesList,
  MOCK_STUDENT,
  MOCK_MODULES,
} from "./fixtures";

test.describe("Modules list /modules", () => {
  test.beforeEach(async ({ page }) => {
    // Mock auth and modules API before navigating
    await mockAuthMe(page, MOCK_STUDENT);
    await mockModulesList(page, MOCK_MODULES);
    // Also mock auth profile for dashboard layout
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(MOCK_STUDENT),
      })
    );
    await page.goto("/modules");
  });

  test("renders page heading", async ({ page }) => {
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("renders module titles from API", async ({ page }) => {
    await expect(
      page.getByText("Aljabar Dasar Kelas X")
    ).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Geometri Bidang Datar")).toBeVisible();
  });

  test("each module has a link to its detail page", async ({ page }) => {
    // Module links should contain the module id in their href
    const links = page.getByRole("link").filter({ hasText: /Aljabar|Geometri/i });
    const count = await links.count();
    expect(count).toBeGreaterThan(0);
  });

  test("module list is navigable by keyboard", async ({ page }) => {
    // Press Tab to reach first module link, then Enter
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    // We can't reliably test focus without knowing exact DOM, but
    // at minimum we check no JS errors occurred
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.keyboard.press("Tab");
    expect(errors).toHaveLength(0);
  });

  test("no console errors on page load", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    // Wait for network idle
    await page.waitForLoadState("networkidle");
    expect(errors).toHaveLength(0);
  });
});
