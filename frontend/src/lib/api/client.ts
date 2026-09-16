/**
 * InklusifMath API Client
 * Handles all HTTP communication with FastAPI backend.
 * Manages JWT tokens with automatic refresh.
 */

import type { AuthTokens, ApiError } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

async function refreshToken(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include', // sends httpOnly cookie
    });
    if (!res.ok) return false;
    const data: AuthTokens = await res.json();
    setAccessToken(data.accessToken);
    return true;
  } catch {
    return false;
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
    (headers as Record<string, string>)['Content-Type'] = 'application/json';
  }

  if (accessToken) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${accessToken}`;
  }

  let res = await fetch(url, { ...options, headers, credentials: 'include' });

  // If 401, try refresh once
  if (res.status === 401 && accessToken) {
    const refreshed = await refreshToken();
    if (refreshed) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${accessToken}`;
      res = await fetch(url, { ...options, headers, credentials: 'include' });
    }
  }

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
    this.name = 'ApiRequestError';
  }
}
