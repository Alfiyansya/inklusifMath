/**
 * Unit tests for modules API mapping logic (lib/api/modules.ts).
 *
 * We mock fetch globally and the firebase auth module to avoid
 * real network calls and browser-only Firebase globals.
 *
 * Tests focus on:
 *   - Snake_case → camelCase field mapping
 *   - fetchModules correct shape
 *   - fetchModuleDetail math_expressions mapping
 *   - ApiRequestError thrown on non-2xx
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock Firebase auth so client.ts doesn't crash in jsdom
vi.mock("@/lib/firebase", () => ({
  auth: { currentUser: null },
}));

import { fetchModules, fetchModuleDetail } from "@/lib/api/modules";
import { ApiRequestError } from "@/lib/api/client";

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeRes(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("fetchModules", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps snake_case to camelCase correctly", async () => {
    const apiPayload = {
      modules: [
        { id: "abc123", title: "Aljabar Dasar", published_at: "2026-01-15T00:00:00" },
        { id: "def456", title: "Geometri", published_at: "2026-02-20T00:00:00" },
      ],
    };
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(apiPayload));

    const modules = await fetchModules();

    expect(modules).toHaveLength(2);
    expect(modules[0]).toEqual({
      id: "abc123",
      title: "Aljabar Dasar",
      publishedAt: "2026-01-15T00:00:00",
    });
    expect(modules[1].id).toBe("def456");
    expect(modules[1].publishedAt).toBe("2026-02-20T00:00:00");
  });

  it("returns empty array when backend returns empty modules list", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes({ modules: [] }));
    const modules = await fetchModules();
    expect(modules).toEqual([]);
  });

  it("throws ApiRequestError on 401", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ detail: "Token tidak valid", error_code: "AUTH_001" }, 401)
    );
    await expect(fetchModules()).rejects.toBeInstanceOf(ApiRequestError);
  });

  it("throws ApiRequestError on 429 with status 429", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ detail: "Rate limit exceeded" }, 429)
    );
    try {
      await fetchModules();
      expect.fail("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiRequestError);
      expect((e as ApiRequestError).status).toBe(429);
    }
  });

  it("throws ApiRequestError on 500", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes({ detail: "Server error" }, 500));
    await expect(fetchModules()).rejects.toBeInstanceOf(ApiRequestError);
  });
});

describe("fetchModuleDetail", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const mockModuleResponse = {
    id: "mod-001",
    title: "Aljabar Linear",
    html_content: "<h2>Bab 1</h2><p>Vektor</p>",
    math_expressions: [
      {
        id: "expr-1",
        original_notation: "x^2 + y^2 = r^2",
        latex: "x^2 + y^2 = r^2",
        ai_narration: "x kuadrat ditambah y kuadrat sama dengan r kuadrat",
        teacher_narration: null,
        status: "ai_generated",
        position_order: 1,
      },
      {
        id: "expr-2",
        original_notation: "\\frac{1}{2}",
        latex: "\\frac{1}{2}",
        ai_narration: "satu per dua",
        teacher_narration: "setengah",
        status: "reviewed",
        position_order: 2,
      },
    ],
  };

  it("maps top-level fields correctly", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockModuleResponse));
    const detail = await fetchModuleDetail("mod-001");

    expect(detail.id).toBe("mod-001");
    expect(detail.title).toBe("Aljabar Linear");
    expect(detail.htmlContent).toBe("<h2>Bab 1</h2><p>Vektor</p>");
  });

  it("maps math_expressions snake_case to camelCase", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockModuleResponse));
    const detail = await fetchModuleDetail("mod-001");

    expect(detail.mathExpressions).toHaveLength(2);
    const expr = detail.mathExpressions[0];
    expect(expr.id).toBe("expr-1");
    expect(expr.originalNotation).toBe("x^2 + y^2 = r^2");
    expect(expr.aiNarration).toBe("x kuadrat ditambah y kuadrat sama dengan r kuadrat");
    expect(expr.teacherNarration).toBeNull();
    expect(expr.positionOrder).toBe(1);
  });

  it("preserves teacher_narration when set", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockModuleResponse));
    const detail = await fetchModuleDetail("mod-001");

    const reviewed = detail.mathExpressions[1];
    expect(reviewed.teacherNarration).toBe("setengah");
    expect(reviewed.status).toBe("reviewed");
  });

  it("throws ApiRequestError on 404", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ detail: "Modul tidak ditemukan" }, 404)
    );
    await expect(fetchModuleDetail("invalid-id")).rejects.toBeInstanceOf(ApiRequestError);
  });
});
