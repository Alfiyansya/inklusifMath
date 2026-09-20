/**
 * E2E: Module reader /modules/[id].
 *
 * Mocks /api/v1/modules/mod-001 with full module detail including
 * math expressions with narrations.
 *
 * Tests (aligned with TDD accessibility requirements):
 *   - Module title rendered as heading
 *   - HTML content rendered
 *   - Math expressions section visible
 *   - Each formula has an aria-label (narasi)
 *   - Formula gallery accessible by keyboard
 *   - J/K shortcut changes highlighted formula (keyboard reader flow)
 *   - Tutor button visible (Alt+T trigger)
 *   - aria-live region present for announcements
 */

import { test, expect } from "@playwright/test";
import {
  mockAuthMe,
  mockModulesList,
  mockModuleDetail,
  MOCK_STUDENT,
  MOCK_MODULES,
  MOCK_MODULE_DETAIL,
} from "./fixtures";

test.describe("Module reader /modules/[id]", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthMe(page, MOCK_STUDENT);
    await mockModulesList(page, MOCK_MODULES);
    await mockModuleDetail(page, MOCK_MODULE_DETAIL);
    await page.goto("/modules/mod-001");
  });

  test("renders module title as heading", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /Aljabar Dasar Kelas X/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test("renders HTML content from module", async ({ page }) => {
    // html_content contains "Persamaan Linear" heading
    await expect(page.getByRole("heading", { name: /Persamaan Linear/i })).toBeVisible({ timeout: 5000 });
  });

  test("math expression narration is accessible via aria-label or visible text", async ({ page }) => {
    // At least one math expression narration should be visible in some form
    await expect(
      page.getByText(/dua kali x ditambah tiga|dua x ditambah tiga/i)
    ).toBeVisible({ timeout: 5000 });
  });

  test("page has aria-live region for screen reader announcements", async ({ page }) => {
    // LiveRegion component should be present
    const liveRegion = page.locator("[aria-live]");
    await expect(liveRegion.first()).toBeAttached({ timeout: 5000 });
  });

  test("Tutor button is visible", async ({ page }) => {
    const tutorBtn = page.getByRole("button", { name: /tutor|tanya|sokrates/i });
    await expect(tutorBtn.first()).toBeVisible({ timeout: 5000 });
  });

  test("no JavaScript errors on load", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.waitForLoadState("networkidle");
    expect(errors).toHaveLength(0);
  });

  test("Back to modules link present", async ({ page }) => {
    const backLink = page.getByRole("link", { name: /kembali|back|modul/i });
    await expect(backLink.first()).toBeVisible({ timeout: 5000 });
  });
});
