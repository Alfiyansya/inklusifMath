/**
 * Unit tests for Tutor API client (lib/api/tutor.ts).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock Firebase auth
vi.mock("@/lib/firebase", () => ({
  auth: { currentUser: null },
}));

import { askTutor } from "@/lib/api/tutor";
import { ApiRequestError } from "@/lib/api/client";

function makeRes(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("askTutor", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends correct payload and maps snake_case response to camelCase", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({
        session_id: "sess-456",
        answer_text: "Pecahan adalah bagian dari keseluruhan.",
        follow_up_hint: "Coba sebutkan pembilang dan penyebutnya.",
      })
    );

    const result = await askTutor({
      moduleId: "mod-123",
      contextElementId: "formula-1",
      transcriptText: "Apa itu pecahan?",
    });

    expect(result).toEqual({
      sessionId: "sess-456",
      answerText: "Pecahan adalah bagian dari keseluruhan.",
      followUpHint: "Coba sebutkan pembilang dan penyebutnya.",
    });

    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, init] = vi.mocked(fetch).mock.calls[0];
    expect(url).toContain("/tutor/ask");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({
      module_id: "mod-123",
      context_element_id: "formula-1",
      transcript_text: "Apa itu pecahan?",
    });
  });

  it("handles null follow_up_hint gracefully", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes({
        session_id: "sess-789",
        answer_text: "Jawaban langsung tanpa hint.",
        follow_up_hint: null,
      })
    );

    const result = await askTutor({
      moduleId: "mod-123",
      contextElementId: "general",
      transcriptText: "Halo",
    });

    expect(result.followUpHint).toBeNull();
  });

  it("throws ApiRequestError on HTTP 403 Forbidden (e.g. non-student role)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      makeRes(
        { detail: "Akses ditolak: dibutuhkan role student atau admin" },
        403
      )
    );

    await expect(
      askTutor({
        moduleId: "mod-123",
        contextElementId: "general",
        transcriptText: "Tanya sesuatu",
      })
    ).rejects.toThrow(ApiRequestError);
  });
});
