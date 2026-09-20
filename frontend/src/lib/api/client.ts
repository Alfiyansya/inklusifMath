/**
 * InklusifMath API Client
 * Handles all HTTP communication with FastAPI backend.
 * Uses Firebase Auth ID tokens for authentication.
 */

import { auth } from "@/lib/firebase";
import type { ApiError } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Get the current Firebase ID token.
 * Returns null if no user is signed in.
 */
async function getIdToken(): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  try {
    return await user.getIdToken();
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    ...(options.headers || {}),
  };

  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  // Attach Firebase ID token
  const token = await getIdToken();
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers, credentials: "include" });

  if (!res.ok) {
    const error: ApiError = await res.json().catch(() => ({
      detail: `Request failed with status ${res.status}`,
    }));
    throw new ApiRequestError(res.status, error.detail, error.errorCode);
  }

  return res.json();
}

export class ApiRequestError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public errorCode?: string,
  ) {
    super(detail);
    this.name = "ApiRequestError";
  }
}
