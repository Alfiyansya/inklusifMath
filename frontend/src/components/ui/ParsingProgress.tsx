"use client";

/**
 * ParsingProgress — Real-time document parsing progress indicator.
 *
 * Primary: SSE via EventSource on GET /api/v1/documents/{documentId}/progress
 * Fallback: Polling GET /api/v1/documents/{documentId} every 5s when SSE
 *           is unavailable (network error on EventSource open).
 *
 * Accessibility: role="status", aria-label, aria-valuenow, aria-valuemax.
 * Status text in Bahasa Indonesia.
 */

import { useEffect, useRef, useState } from "react";
import { apiRequest } from "@/lib/api/client";

// ── Status labels ─────────────────────────────────────────────────────────────

type ParsingStatus = "queued" | "processing" | "done" | "error" | string;

const STATUS_LABELS: Record<string, string> = {
  queued: "Antrian...",
  processing: "Memproses dokumen...",
  done: "Selesai!",
  error: "Gagal memproses dokumen",
};

function getStatusLabel(status: ParsingStatus): string {
  return STATUS_LABELS[status] ?? "Memproses...";
}

// ── Progress estimate per status (when backend doesn't send progress field) ──

const STATUS_PROGRESS: Record<string, number> = {
  queued: 10,
  processing: 55,
  done: 100,
  error: 100,
};

// ── Poll response shape ───────────────────────────────────────────────────────

interface DocumentStatusResponse {
  parsing_status: string;
  [key: string]: unknown;
}

// ── SSE event shapes ──────────────────────────────────────────────────────────

interface ProgressEventData {
  status?: ParsingStatus;
  progress?: number; // 0–100
  message?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

interface ParsingProgressProps {
  /** The document ID to track */
  documentId: string;
  /** Called when parsing is complete (or errored) — passes the final status */
  onComplete: (status: string) => void;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function ParsingProgress({ documentId, onComplete }: ParsingProgressProps) {
  const [progress, setProgress] = useState(10);
  const [status, setStatus] = useState<ParsingStatus>("queued");
  const [isDone, setIsDone] = useState(false);

  const esRef = useRef<EventSource | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  // ── Helpers ────────────────────────────────────────────────────────────────

  function cleanup() {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }

  function handleTerminal(finalStatus: string) {
    setIsDone(true);
    setProgress(100);
    setStatus(finalStatus);
    cleanup();
    onCompleteRef.current(finalStatus);
  }

  // ── Polling fallback ───────────────────────────────────────────────────────

  function startPolling() {
    async function poll() {
      try {
        const data = await apiRequest<DocumentStatusResponse>(
          `/documents/${documentId}`
        );
        const s = data.parsing_status ?? "processing";
        setStatus(s);
        setProgress(STATUS_PROGRESS[s] ?? 55);
        if (s === "done" || s === "error") {
          handleTerminal(s);
        }
      } catch {
        // Ignore transient errors — keep polling
      }
    }

    poll(); // Run immediately
    pollTimerRef.current = setInterval(poll, 5000);
  }

  // ── SSE connection ─────────────────────────────────────────────────────────

  useEffect(() => {
    if (!documentId) return;

    const sseUrl = `${API_BASE_URL}/documents/${documentId}/progress`;

    let sseConnected = false;

    try {
      const es = new EventSource(sseUrl, { withCredentials: true });
      esRef.current = es;

      es.onopen = () => {
        sseConnected = true;
      };

      es.onmessage = (event: MessageEvent) => {
        sseConnected = true;
        try {
          const data: ProgressEventData = JSON.parse(event.data as string);
          const s = data.status ?? "processing";
          const p = data.progress ?? STATUS_PROGRESS[s] ?? 55;
          setStatus(s);
          setProgress(p);

          if (s === "done" || s === "error") {
            handleTerminal(s);
          }
        } catch {
          // Malformed SSE data — ignore
        }
      };

      // Named event variants some backends emit
      es.addEventListener("progress", (event: MessageEvent) => {
        if (es.onmessage) es.onmessage(event);
      });

      es.onerror = () => {
        es.close();
        esRef.current = null;

        if (!sseConnected) {
          // SSE not supported / connection refused — switch to polling
          startPolling();
        } else {
          // Transient SSE error after connect — also fall back to polling
          startPolling();
        }
      };
    } catch {
      // EventSource constructor threw (very old browser) — fall back to polling
      startPolling();
    }

    return () => {
      cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  // ── Render ─────────────────────────────────────────────────────────────────

  const isError = status === "error";
  const label = getStatusLabel(status);
  const barColor = isError
    ? "var(--color-error, #ef4444)"
    : status === "done"
    ? "var(--color-success, #22c55e)"
    : "var(--color-primary)";

  return (
    <div
      role="status"
      aria-label={`Status pemrosesan dokumen: ${label}`}
      aria-live="polite"
      className="rounded-xl px-5 py-4 mb-6"
      style={{ border: "1px solid var(--color-border-card)", backgroundColor: "var(--color-bg-page, #f8fafc)" }}
    >
      {/* Status row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {/* Animated spinner when processing */}
          {!isDone && !isError && (
            <span
              className="inline-block w-3 h-3 rounded-full animate-pulse"
              style={{ backgroundColor: "var(--color-primary)" }}
              aria-hidden="true"
            />
          )}
          {isError && (
            <span aria-hidden="true" className="text-sm">⚠️</span>
          )}
          {isDone && !isError && (
            <span aria-hidden="true" className="text-sm">✅</span>
          )}
          <span
            className="text-sm font-medium"
            style={{ color: isError ? "var(--color-error, #ef4444)" : "var(--color-text-primary, #1e293b)" }}
          >
            {label}
          </span>
        </div>
        <span className="text-xs font-mono" style={{ color: "var(--color-text-muted, #94a3b8)" }}>
          {progress}%
        </span>
      </div>

      {/* Progress bar */}
      <div
        className="h-2 rounded-full overflow-hidden"
        style={{ backgroundColor: "var(--color-border-card, #e2e8f0)" }}
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Kemajuan pemrosesan: ${progress}%`}
      >
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${progress}%`,
            backgroundColor: barColor,
          }}
        />
      </div>

      {/* Error hint */}
      {isError && (
        <p className="mt-2 text-xs" style={{ color: "var(--color-text-muted, #94a3b8)" }}>
          Dokumen gagal diproses. Coba unggah ulang atau hubungi administrator.
        </p>
      )}
    </div>
  );
}
