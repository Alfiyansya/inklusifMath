/**
 * Unit tests for documents API mapping logic (lib/api/documents.ts).
 *
 * Tests the snake_case → camelCase field mapping for:
 *   - uploadDocument
 *   - fetchDocumentNarrations
 *   - updateNarration
 *   - approveDocument
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock Firebase auth
vi.mock("@/lib/firebase", () => ({
  auth: { currentUser: null },
}));

import {
  uploadDocument,
  fetchDocumentNarrations,
  updateNarration,
  approveDocument,
  fetchDocumentList,
  fetchDocumentDetail,
} from "@/lib/api/documents";
import { ApiRequestError } from "@/lib/api/client";

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeRes(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ── uploadDocument ────────────────────────────────────────────────────────────

describe("uploadDocument", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps snake_case response to camelCase", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({
        document_id: "doc-123",
        title: "Matematika Kelas X",
        status: "processing",
        message: "Dokumen sedang diproses",
      })
    );

    const file = new File(["content"], "test.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const result = await uploadDocument(file, "Matematika Kelas X");

    expect(result.documentId).toBe("doc-123");
    expect(result.title).toBe("Matematika Kelas X");
    expect(result.status).toBe("processing");
    expect(result.message).toBe("Dokumen sedang diproses");
  });

  it("sends FormData (no Content-Type override)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ document_id: "d1", title: "T", status: "processing", message: "ok" })
    );
    const file = new File(["x"], "a.pdf", { type: "application/pdf" });
    await uploadDocument(file, "Test");

    const callArgs = vi.mocked(fetch).mock.calls[0];
    const body = (callArgs[1] as RequestInit)?.body;
    expect(body).toBeInstanceOf(FormData);
  });

  it("throws ApiRequestError on 413 (file too large)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes({ detail: "Ukuran file terlalu besar" }, 413));
    const file = new File(["x"], "big.pdf", { type: "application/pdf" });
    await expect(uploadDocument(file, "Big")).rejects.toBeInstanceOf(ApiRequestError);
  });

  it("throws ApiRequestError on 429 (rate limited)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes({ detail: "Rate limit" }, 429));
    const file = new File(["x"], "a.pdf", { type: "application/pdf" });
    await expect(uploadDocument(file, "Test")).rejects.toBeInstanceOf(ApiRequestError);
  });
});

// ── fetchDocumentNarrations ───────────────────────────────────────────────────

describe("fetchDocumentNarrations", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const mockNarrationResponse = {
    document_id: "doc-abc",
    title: "Dokumen Test",
    expressions: [
      {
        id: "expr-1",
        original_notation: "x^2",
        latex: "x^2",
        ai_narration: "x kuadrat",
        teacher_narration: "x pangkat dua",
        status: "reviewed",
        position_order: 1,
      },
    ],
  };

  it("maps document_id and title", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockNarrationResponse));
    const result = await fetchDocumentNarrations("doc-abc");

    expect(result.documentId).toBe("doc-abc");
    expect(result.title).toBe("Dokumen Test");
  });

  it("maps expressions snake_case to camelCase", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockNarrationResponse));
    const result = await fetchDocumentNarrations("doc-abc");

    expect(result.expressions).toHaveLength(1);
    const expr = result.expressions[0];
    expect(expr.originalNotation).toBe("x^2");
    expect(expr.aiNarration).toBe("x kuadrat");
    expect(expr.teacherNarration).toBe("x pangkat dua");
    expect(expr.positionOrder).toBe(1);
  });

  it("returns empty expressions array", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ document_id: "d1", title: "T", expressions: [] })
    );
    const result = await fetchDocumentNarrations("d1");
    expect(result.expressions).toEqual([]);
  });

  it("throws ApiRequestError on 404", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes({ detail: "Not found" }, 404));
    await expect(fetchDocumentNarrations("bad-id")).rejects.toBeInstanceOf(ApiRequestError);
  });
});

// ── updateNarration ───────────────────────────────────────────────────────────

describe("updateNarration", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps teacher_narration response correctly", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({
        id: "expr-1",
        status: "reviewed",
        teacher_narration: "nilai mutlak dari x",
      })
    );

    const result = await updateNarration("expr-1", "nilai mutlak dari x");
    expect(result.id).toBe("expr-1");
    expect(result.status).toBe("reviewed");
    expect(result.teacherNarration).toBe("nilai mutlak dari x");
  });

  it("sends PATCH with JSON body containing teacher_narration", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ id: "e1", status: "reviewed", teacher_narration: "test" })
    );
    await updateNarration("e1", "test narration");

    const callArgs = vi.mocked(fetch).mock.calls[0];
    const options = callArgs[1] as RequestInit;
    expect(options.method).toBe("PATCH");
    const body = JSON.parse(options.body as string);
    expect(body.teacher_narration).toBe("test narration");
  });
});

// ── approveDocument ───────────────────────────────────────────────────────────

describe("approveDocument", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps approve response snake_case to camelCase", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({
        module_id: "mod-999",
        document_id: "doc-123",
        is_published: true,
        published_at: "2026-09-17T10:00:00",
      })
    );

    const result = await approveDocument("doc-123");
    expect(result.moduleId).toBe("mod-999");
    expect(result.documentId).toBe("doc-123");
    expect(result.isPublished).toBe(true);
    expect(result.publishedAt).toBe("2026-09-17T10:00:00");
  });

  it("sends POST request to correct URL", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ module_id: "m1", document_id: "d1", is_published: true, published_at: "2026-01-01" })
    );
    await approveDocument("doc-xyz");

    const callArgs = vi.mocked(fetch).mock.calls[0];
    const url = callArgs[0] as string;
    expect(url).toContain("/documents/doc-xyz/approve");
    expect((callArgs[1] as RequestInit).method).toBe("POST");
  });

  it("throws ApiRequestError on 403 (not teacher)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes({ detail: "Forbidden" }, 403));
    await expect(approveDocument("doc-123")).rejects.toBeInstanceOf(ApiRequestError);
  });
});

// ── fetchDocumentList ─────────────────────────────────────────────────────────

describe("fetchDocumentList", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const mockListResponse = {
    documents: [
      {
        document_id: "doc-list-1",
        title: "Geometri Dasar",
        file_type: "pdf",
        parsing_status: "parsed",
        ocr_used: "none",
        math_expressions_count: 12,
        is_published: true,
        module_id: "mod-42",
        created_at: "2026-09-01T00:00:00",
        updated_at: "2026-09-02T00:00:00",
      },
    ],
    total: 1,
    limit: 50,
    offset: 0,
  };

  it("maps snake_case document fields to camelCase", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockListResponse));
    const result = await fetchDocumentList();

    expect(result.documents).toHaveLength(1);
    const doc = result.documents[0];
    expect(doc.documentId).toBe("doc-list-1");
    expect(doc.title).toBe("Geometri Dasar");
    expect(doc.fileType).toBe("pdf");
    expect(doc.parsingStatus).toBe("parsed");
    expect(doc.ocrUsed).toBe("none");
    expect(doc.mathExpressionsCount).toBe(12);
    expect(doc.isPublished).toBe(true);
    expect(doc.moduleId).toBe("mod-42");
    expect(doc.createdAt).toBe("2026-09-01T00:00:00");
    expect(doc.updatedAt).toBe("2026-09-02T00:00:00");
  });

  it("returns total, limit, and offset from response", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ ...mockListResponse, total: 99, limit: 25, offset: 25 })
    );
    const result = await fetchDocumentList(25, 25);

    expect(result.total).toBe(99);
    expect(result.limit).toBe(25);
    expect(result.offset).toBe(25);
  });

  it("handles empty document list", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({ documents: [], total: 0, limit: 50, offset: 0 })
    );
    const result = await fetchDocumentList();

    expect(result.documents).toEqual([]);
    expect(result.total).toBe(0);
  });
});

// ── fetchDocumentDetail ───────────────────────────────────────────────────────

describe("fetchDocumentDetail", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const mockDetailResponse = {
    document_id: "doc-detail-1",
    title: "Statistika Lanjut",
    file_type: "docx",
    parsing_status: "parsed",
    ocr_used: "none",
    error_code: null,
    math_expressions_count: 8,
    narrations_pending: 3,
    narrations_ai_generated: 2,
    narrations_reviewed: 2,
    narrations_approved: 1,
    is_published: false,
    module_id: null,
    published_at: null,
    created_at: "2026-09-10T00:00:00",
    updated_at: "2026-09-11T00:00:00",
  };

  it("maps all snake_case fields to camelCase", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockDetailResponse));
    const result = await fetchDocumentDetail("doc-detail-1");

    expect(result.documentId).toBe("doc-detail-1");
    expect(result.title).toBe("Statistika Lanjut");
    expect(result.fileType).toBe("docx");
    expect(result.parsingStatus).toBe("parsed");
    expect(result.ocrUsed).toBe("none");
    expect(result.mathExpressionsCount).toBe(8);
    expect(result.isPublished).toBe(false);
    expect(result.createdAt).toBe("2026-09-10T00:00:00");
    expect(result.updatedAt).toBe("2026-09-11T00:00:00");
  });

  it("preserves null fields (errorCode, moduleId, publishedAt)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockDetailResponse));
    const result = await fetchDocumentDetail("doc-detail-1");

    expect(result.errorCode).toBeNull();
    expect(result.moduleId).toBeNull();
    expect(result.publishedAt).toBeNull();
  });

  it("maps all narration count fields correctly", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(makeRes(mockDetailResponse));
    const result = await fetchDocumentDetail("doc-detail-1");

    expect(result.narrationsPending).toBe(3);
    expect(result.narrationsAiGenerated).toBe(2);
    expect(result.narrationsReviewed).toBe(2);
    expect(result.narrationsApproved).toBe(1);
  });
});
