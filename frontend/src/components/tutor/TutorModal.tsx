"use client";

/**
 * TutorModal — Accessible Socratic AI tutor dialog.
 *
 * Implements:
 *   - FR-11: Alt+T global shortcut (via useTutor hook)
 *   - FR-14: Push-to-Talk voice input (Web Speech API, lang=id-ID)
 *   - FR-15: aria-live live region for screen reader announcements
 *   - ADR-005: Focus trapping per WCAG 2.1 SC 2.4.3
 *   - FR-17: Earcon audio feedback (earcon wired in useTutor)
 *   - Graceful fallback: text input when speech unavailable
 *
 * Focus trapping:
 *   - useEffect attaches keydown handler for Tab/Shift+Tab cycling
 *   - First focusable element receives focus on open
 *   - Escape closes modal and returns focus to trigger
 *   - Portal via React createPortal to body (z-index: 50)
 *
 * Screen reader announcement:
 *   - role="dialog" + aria-modal="true" + aria-labelledby
 *   - LiveRegion (aria-live="assertive") for tutor responses
 *   - Each message announced when appended
 */

import { useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { LiveRegion } from "@/components/ui/LiveRegion";
import type { TutorMessage, TutorStatus } from "@/hooks/useTutor";

// ── Focus trap helpers ────────────────────────────────────────────────────────

const FOCUSABLE_SELECTORS = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(", ");

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS));
}

// ── Status icon ───────────────────────────────────────────────────────────────

function StatusDot({ status }: { status: TutorStatus }) {
  const colors: Record<TutorStatus, string> = {
    idle: "bg-gray-300",
    listening: "bg-red-500 animate-pulse",
    processing: "bg-yellow-400 animate-pulse",
    answered: "bg-green-500",
    error: "bg-red-600",
  };
  const labels: Record<TutorStatus, string> = {
    idle: "Siap",
    listening: "Merekam…",
    processing: "Memproses…",
    answered: "Selesai",
    error: "Error",
  };
  return (
    <span className="flex items-center gap-1.5 text-xs text-text-muted font-medium">
      <span className={`inline-block w-2 h-2 rounded-full ${colors[status]}`} aria-hidden="true" />
      {labels[status]}
    </span>
  );
}

// ── Single chat bubble ────────────────────────────────────────────────────────

function ChatBubble({ msg }: { msg: TutorMessage }) {
  const isStudent = msg.role === "student";
  return (
    <div className={`flex ${isStudent ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isStudent
            ? "bg-primary text-white rounded-br-sm"
            : "bg-bg-page text-text-primary rounded-bl-sm"
        }`}
        style={isStudent ? {} : { border: "1px solid var(--color-border-card)" }}
        role={isStudent ? undefined : "note"}
        aria-label={isStudent ? undefined : `Tutor: ${msg.text}`}
      >
        {!isStudent && (
          <p className="text-xs font-bold mb-1" style={{ color: "var(--color-primary)" }}>
            Tutor Sokrates
          </p>
        )}
        <p>{msg.text}</p>
        {msg.hint && (
          <p
            className="mt-2 text-xs italic opacity-80"
            aria-label={`Pertanyaan pemandu: ${msg.hint}`}
          >
            💭 {msg.hint}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface TutorModalProps {
  isOpen: boolean;
  status: TutorStatus;
  messages: TutorMessage[];
  transcript: string;
  liveAnnouncement: string;
  isSpeechSupported: boolean;
  /** MediaRecorder available — backend STT fallback */
  isRecorderSupported?: boolean;
  onClose: () => void;
  onTranscriptChange: (t: string) => void;
  onStartListening: () => void;
  onStopListening: () => void;
  onSubmit: () => Promise<void>;
  onClear: () => void;
  /** Element that triggered the modal — receives focus on close */
  triggerRef?: React.RefObject<HTMLElement | null>;
}

// ── Main Modal ────────────────────────────────────────────────────────────────

export function TutorModal({
  isOpen,
  status,
  messages,
  transcript,
  liveAnnouncement,
  isSpeechSupported,
  isRecorderSupported = false,
  onClose,
  onTranscriptChange,
  onStartListening,
  onStopListening,
  onSubmit,
  onClear,
  triggerRef,
}: TutorModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const isListening = status === "listening";
  const isProcessing = status === "processing";
  const titleId = "tutor-modal-title";

  // ── Focus trap ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isOpen) return;

    const dialog = dialogRef.current;
    if (!dialog) return;

    // Move focus to first focusable element (textarea or close button)
    const focusables = getFocusableElements(dialog);
    focusables[0]?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        triggerRef?.current?.focus();
        return;
      }

      if (e.key !== "Tab") return;

      const focusable = getFocusableElements(dialog);
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement;

      if (e.shiftKey) {
        // Shift+Tab: wrap from first → last
        if (active === first || !dialog.contains(active)) {
          e.preventDefault();
          last.focus();
        }
      } else {
        // Tab: wrap from last → first
        if (active === last || !dialog.contains(active)) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, triggerRef]);

  // Auto-scroll messages
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Keyboard submit: Enter (without Shift) in textarea
  const handleTextareaKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey && !isProcessing) {
        e.preventDefault();
        onSubmit();
      }
    },
    [onSubmit, isProcessing]
  );

  if (!isOpen) return null;

  const modal = (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        aria-hidden="true"
        onClick={onClose}
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
      >
        <div
          className="bg-white rounded-2xl w-full max-w-lg shadow-xl flex flex-col"
          style={{
            border: "1px solid var(--color-border-card)",
            maxHeight: "85vh",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-5 py-4"
            style={{ borderBottom: "1px solid var(--color-border-card)" }}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-lg"
                style={{ backgroundColor: "rgba(100,149,237,0.1)" }}
                aria-hidden="true"
              >
                🦉
              </div>
              <div>
                <h2
                  id={titleId}
                  className="text-base font-bold text-text-primary"
                >
                  Tutor Sokrates
                </h2>
                <p className="text-xs text-text-muted">
                  Saya akan membantumu berpikir, bukan memberi jawaban langsung.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <StatusDot status={status} />
              <button
                onClick={onClose}
                aria-label="Tutup Tutor Sokrates"
                className="w-8 h-8 rounded-full flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-page transition-colors focus-visible:ring-2 focus-visible:ring-primary"
              >
                ✕
              </button>
            </div>
          </div>

          {/* aria-live region — screen reader announcements */}
          <LiveRegion message={liveAnnouncement} politeness="assertive" />

          {/* Messages */}
          <div
            className="flex-1 overflow-y-auto px-5 py-4 min-h-[180px]"
            role="log"
            aria-label="Riwayat percakapan dengan Tutor Sokrates"
            aria-live="polite"
          >
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-8">
                <span className="text-4xl mb-3" aria-hidden="true">🦉</span>
                <p className="text-text-secondary text-sm max-w-[260px] leading-relaxed">
                  Halo! Aku Tutor Sokrates. Punya pertanyaan tentang materi yang baru kamu baca? Tanyakan padaku!
                </p>
                {!isSpeechSupported && !isRecorderSupported && (
                  <p className="text-xs text-text-muted mt-3 max-w-[240px]">
                    ℹ️ Browsermu tidak mendukung input suara. Ketik pertanyaanmu di bawah.
                  </p>
                )}
                {!isSpeechSupported && isRecorderSupported && (
                  <p className="text-xs text-text-muted mt-3 max-w-[240px]">
                    🎙️ Rekam suaramu, lalu server akan mentranskripnya.
                  </p>
                )}
              </div>
            ) : (
              <>
                {messages.map((msg, i) => (
                  <ChatBubble key={i} msg={msg} />
                ))}
                {isProcessing && (
                  <div className="flex justify-start mb-3">
                    <div
                      className="bg-bg-page rounded-2xl rounded-bl-sm px-4 py-3"
                      style={{ border: "1px solid var(--color-border-card)" }}
                      aria-label="Tutor sedang mengetik…"
                    >
                      <span className="inline-flex gap-1" aria-hidden="true">
                        {[0, 1, 2].map((i) => (
                          <span
                            key={i}
                            className="w-2 h-2 bg-primary rounded-full animate-bounce"
                            style={{ animationDelay: `${i * 0.15}s` }}
                          />
                        ))}
                      </span>
                    </div>
                  </div>
                )}
                <div ref={messageEndRef} aria-hidden="true" />
              </>
            )}
          </div>

          {/* Input area */}
          <div
            className="px-5 py-4"
            style={{ borderTop: "1px solid var(--color-border-card)" }}
          >
            {/* Transcript preview when listening */}
            {isListening && transcript && (
              <div
                className="mb-2 text-xs text-text-muted italic px-1"
                aria-live="polite"
                aria-label={`Transkrip sementara: ${transcript}`}
              >
                🎙️ &ldquo;{transcript}&rdquo;
              </div>
            )}

            <div className="flex gap-2 items-end">
              <textarea
                ref={inputRef}
                value={transcript}
                onChange={(e) => onTranscriptChange(e.target.value)}
                onKeyDown={handleTextareaKeyDown}
                placeholder="Ketik pertanyaanmu, atau tekan Rekam…"
                rows={2}
                disabled={isProcessing || isListening}
                className="flex-1 resize-none rounded-xl px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 transition-colors"
                style={{
                  border: "1px solid var(--color-border-card)",
                  backgroundColor: "var(--color-bg-page)",
                }}
                aria-label="Ketik pertanyaanmu"
                aria-describedby="tutor-shortcut-hint"
              />

              <div className="flex flex-col gap-2 shrink-0">
                {/* Voice button — shown for both Web Speech API and MediaRecorder */}
                {(isSpeechSupported || isRecorderSupported) && (
                  <button
                    onClick={isListening ? onStopListening : onStartListening}
                    disabled={isProcessing}
                    aria-label={isListening ? "Hentikan rekaman" : "Mulai rekam suara"}
                    aria-pressed={isListening}
                    className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 ${
                      isListening
                        ? "bg-red-500 text-white"
                        : "text-text-secondary hover:bg-bg-page"
                    }`}
                    style={
                      isListening
                        ? {}
                        : { border: "1px solid var(--color-border-card)" }
                    }
                  >
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill={isListening ? "currentColor" : "none"}
                      stroke="currentColor"
                      strokeWidth="2"
                      aria-hidden="true"
                    >
                      <rect x="9" y="2" width="6" height="12" rx="3" />
                      <path d="M5 10a7 7 0 0014 0M12 19v3M9 22h6" />
                    </svg>
                  </button>
                )}

                {/* Send button */}
                <button
                  onClick={onSubmit}
                  disabled={isProcessing || isListening || !transcript.trim()}
                  aria-label="Kirim pertanyaan ke Tutor"
                  className="w-10 h-10 rounded-xl flex items-center justify-center bg-primary text-white transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-40"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    aria-hidden="true"
                  >
                    <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Footer hints */}
            <div
              id="tutor-shortcut-hint"
              className="flex items-center justify-between mt-2"
            >
              <p className="text-xs text-text-muted">
                <kbd className="bg-bg-page border border-border-card rounded px-1 font-mono text-xs">Enter</kbd>{" "}
                kirim &nbsp;·&nbsp;{" "}
                <kbd className="bg-bg-page border border-border-card rounded px-1 font-mono text-xs">Shift+Enter</kbd>{" "}
                baris baru &nbsp;·&nbsp;{" "}
                <kbd className="bg-bg-page border border-border-card rounded px-1 font-mono text-xs">Esc</kbd>{" "}
                tutup
              </p>
              {messages.length > 0 && (
                <button
                  onClick={onClear}
                  className="text-xs text-text-muted hover:text-text-primary transition-colors underline"
                >
                  Hapus percakapan
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );

  return typeof document !== "undefined"
    ? createPortal(modal, document.body)
    : null;
}
