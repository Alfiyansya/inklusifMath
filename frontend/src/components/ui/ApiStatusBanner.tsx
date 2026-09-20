/**
 * ApiStatusBanner — Shows when frontend is using mock data
 * because the backend API is not yet connected.
 * Accessible: uses role="status" for screen reader announcement.
 */

"use client";

interface ApiStatusBannerProps {
  /** Short message explaining what is using mock data */
  context?: string;
}

export function ApiStatusBanner({
  context = "Data ditampilkan adalah data contoh",
}: ApiStatusBannerProps) {
  return (
    <div
      role="status"
      className="rounded-lg px-4 py-2.5 text-sm flex items-center gap-2 mb-4"
      style={{
        backgroundColor: "rgba(245, 158, 11, 0.1)",
        border: "1px solid rgba(245, 158, 11, 0.3)",
        color: "var(--color-text-secondary)",
      }}
    >
      <span aria-hidden="true" className="text-base">⚠️</span>
      <span>
        <strong style={{ color: "var(--color-warning)" }}>Mode Pengembangan:</strong>{" "}
        {context} karena backend API belum terhubung.
      </span>
    </div>
  );
}
