/**
 * Unit tests for ApiRequestError (lib/api/client.ts).
 *
 * Tests the error class construction, message propagation, and optional fields.
 * No Firebase or network mocking needed — class is pure logic.
 */

import { describe, it, expect, vi } from "vitest";

// Mock Firebase so the module can be imported without real credentials
vi.mock("@/lib/firebase", () => ({
  auth: { currentUser: null },
}));

import { ApiRequestError } from "@/lib/api/client";

describe("ApiRequestError", () => {
  it("sets status, detail, and name correctly", () => {
    const err = new ApiRequestError(429, "Terlalu banyak permintaan");
    expect(err.status).toBe(429);
    expect(err.detail).toBe("Terlalu banyak permintaan");
    expect(err.name).toBe("ApiRequestError");
  });

  it("inherits from Error — message equals detail", () => {
    const err = new ApiRequestError(404, "Dokumen tidak ditemukan");
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toBe("Dokumen tidak ditemukan");
  });

  it("stores optional errorCode when provided", () => {
    const err = new ApiRequestError(400, "File tidak valid", "DOC_001");
    expect(err.errorCode).toBe("DOC_001");
  });

  it("errorCode is undefined when not provided", () => {
    const err = new ApiRequestError(500, "Server error");
    expect(err.errorCode).toBeUndefined();
  });

  it("handles 401 Unauthorized", () => {
    const err = new ApiRequestError(401, "Token tidak valid", "AUTH_001");
    expect(err.status).toBe(401);
    expect(err.errorCode).toBe("AUTH_001");
  });

  it("handles 429 rate limit", () => {
    const err = new ApiRequestError(429, "Rate limit exceeded");
    expect(err.status).toBe(429);
  });

  it("stack trace is available (standard Error behaviour)", () => {
    const err = new ApiRequestError(500, "Server error");
    expect(err.stack).toBeDefined();
  });
});
