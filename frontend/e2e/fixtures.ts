/**
 * Shared Playwright fixtures and helpers for InklusifMath E2E tests.
 *
 * Key helpers:
 *   - mockFirebaseAuth()  — mock Firebase Auth so we skip real login
 *   - mockApi()           — mock FastAPI responses via route interception
 *   - MOCK_STUDENT/TEACHER — standard fake users for tests
 */

import { test as base, Page, Route } from "@playwright/test";

// ── Mock data ─────────────────────────────────────────────────────────────────

export const MOCK_STUDENT = {
  id: "student-uid-001",
  email: "siswa@inklusif.test",
  role: "student",
  full_name: "Ahmad Zaidan",
  student_level: "smp",
  firebase_uid: "student-uid-001",
};

export const MOCK_TEACHER = {
  id: "teacher-uid-001",
  email: "guru@inklusif.test",
  role: "teacher",
  full_name: "Ibu Siti",
  student_level: null,
  firebase_uid: "teacher-uid-001",
};

export const MOCK_MODULES = {
  modules: [
    { id: "mod-001", title: "Aljabar Dasar Kelas X", published_at: "2026-01-15T00:00:00" },
    { id: "mod-002", title: "Geometri Bidang Datar", published_at: "2026-02-20T00:00:00" },
  ],
};

export const MOCK_MODULE_DETAIL = {
  id: "mod-001",
  title: "Aljabar Dasar Kelas X",
  html_content: "<h2>Persamaan Linear</h2><p>Persamaan linear adalah ...</p>",
  math_expressions: [
    {
      id: "expr-001",
      original_notation: "2x + 3 = 7",
      latex: "2x + 3 = 7",
      ai_narration: "dua x ditambah tiga sama dengan tujuh",
      teacher_narration: "dua kali x ditambah tiga sama dengan tujuh",
      status: "reviewed",
      position_order: 1,
    },
    {
      id: "expr-002",
      original_notation: "\\frac{a}{b}",
      latex: "\\frac{a}{b}",
      ai_narration: "a per b",
      teacher_narration: null,
      status: "ai_generated",
      position_order: 2,
    },
  ],
};

// ── Route helpers ─────────────────────────────────────────────────────────────

export async function mockApiRoute(
  page: Page,
  urlPattern: string | RegExp,
  response: unknown,
  status = 200,
): Promise<void> {
  await page.route(urlPattern, (route: Route) => {
    route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });
}

/** Mock the /auth/me endpoint to return a given user profile. */
export async function mockAuthMe(page: Page, user: typeof MOCK_STUDENT | typeof MOCK_TEACHER) {
  await mockApiRoute(page, "**/api/v1/auth/me", user);
}

/** Mock modules list endpoint. */
export async function mockModulesList(page: Page, modules = MOCK_MODULES) {
  await mockApiRoute(page, "**/api/v1/modules", modules);
}

/** Mock module detail endpoint. */
export async function mockModuleDetail(page: Page, detail = MOCK_MODULE_DETAIL) {
  await mockApiRoute(page, /\/api\/v1\/modules\/mod-001/, detail);
}

/** Mock tutor/ask endpoint. */
export async function mockTutorAsk(page: Page, answer = "Coba pikirkan, apa yang terjadi jika x = 2?") {
  await mockApiRoute(page, "**/api/v1/tutor/ask", { answer });
}

// ── Extended test fixture ─────────────────────────────────────────────────────

export const test = base.extend<{
  mockStudent: void;
  mockTeacher: void;
}>({
  // Fixture: auto-mock /auth/me as student
  mockStudent: [
    async ({ page }, use) => {
      await mockAuthMe(page, MOCK_STUDENT);
      await use();
    },
    { auto: false },
  ],

  // Fixture: auto-mock /auth/me as teacher
  mockTeacher: [
    async ({ page }, use) => {
      await mockAuthMe(page, MOCK_TEACHER);
      await use();
    },
    { auto: false },
  ],
});

export { expect } from "@playwright/test";
