"use client";

/**
 * NarrationCard — teacher review card for a single math expression.
 *
 * Layout: 2-column grid
 *   Left  — MathJax rendered formula + raw LaTeX (collapsible) + AI confidence
 *   Right — Editable narasi textarea + Save + Approve buttons
 *
 * State machine per card:
 *   unsaved → (edit) → dirty → (save) → saved/reviewed → (approve) → approved
 */

import React, { useState } from "react";
import { MathDisplay } from "@/components/math";

interface NarrationCardProps {
  index: number;
  originalNotation: string;
  latex: string;
  aiNarration: string;
  aiConfidence: number; // 0–100
  teacherNarration?: string;
  isApproved?: boolean;
  isSaving?: boolean;
  needsAttention?: boolean;
  onNarrationChange?: (value: string) => void;
  onSave?: () => Promise<void>;
  onApprove?: () => void;
}

export const NarrationCard: React.FC<NarrationCardProps> = ({
  index,
  originalNotation,
  latex,
  aiNarration,
  aiConfidence,
  teacherNarration,
  isApproved,
  isSaving = false,
  needsAttention = false,
  onNarrationChange,
  onSave,
  onApprove,
}) => {
  const isLowConfidence = aiConfidence < 95;
  const currentNarration = teacherNarration ?? aiNarration;
  const [localSaving, setLocalSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);

  const handleSave = async () => {
    if (!onSave) return;
    setLocalSaving(true);
    try {
      await onSave();
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 2000);
    } finally {
      setLocalSaving(false);
    }
  };

  const saving = isSaving || localSaving;

  return (
    <article
      aria-label={`Rumus ${index}: ${originalNotation}`}
      className={`bg-white border-2 rounded-xl overflow-hidden mb-6 transition-colors ${
        isApproved
          ? "border-success/50"
          : needsAttention
          ? "border-warning"
          : "border-border-card"
      }`}
    >
      {/* Card header */}
      <div className="bg-bg-page px-5 py-3 flex justify-between items-center border-b border-border-card">
        <div className="flex items-center gap-3">
          <span className="bg-white border border-border-card rounded px-2 py-0.5 text-xs font-mono text-text-secondary">
            #{index}
          </span>
          <span className="font-medium text-text-primary">{originalNotation}</span>
        </div>
        <div className="flex items-center gap-2">
          {isApproved && (
            <span className="bg-success/10 text-success text-xs font-medium px-2 py-1 rounded flex items-center gap-1">
              ✓ Disetujui
            </span>
          )}
          {needsAttention && !isApproved && (
            <span className="bg-warning/10 text-warning text-xs font-medium px-2 py-1 rounded">
              ⚠ Perlu Perhatian
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 divide-x divide-border-card">
        {/* ── Left Column: Visual Preview ── */}
        <div className="p-5">
          <p className="uppercase text-xs tracking-wider text-text-muted font-semibold mb-3">
            TAMPILAN VISUAL (MATHJAX)
          </p>

          {/* MathJax rendered formula */}
          <div
            className="bg-bg-page rounded-lg p-4 mb-4 flex items-center justify-center min-h-[72px]"
            style={{ border: "1px solid var(--color-border-card)" }}
          >
            {latex ? (
              <MathDisplay
                latex={latex}
                teacherNarration={teacherNarration}
                aiNarration={aiNarration}
                display={false}
              />
            ) : (
              <span className="text-text-muted text-sm italic">
                Tidak ada formula LaTeX
              </span>
            )}
          </div>

          {/* Collapsible raw LaTeX */}
          <details className="group">
            <summary className="cursor-pointer text-xs text-text-muted hover:text-text-secondary select-none mb-1">
              Lihat kode LaTeX ▾
            </summary>
            <div className="bg-bg-page rounded p-2 font-mono text-xs text-text-secondary overflow-x-auto mt-1 break-all">
              {latex || <em>—</em>}
            </div>
          </details>

          <p className="text-xs text-text-muted mt-3">
            Keyakinan AI:{" "}
            <span
              className={
                isLowConfidence ? "font-bold text-warning" : "font-medium text-success"
              }
            >
              {aiConfidence}%
            </span>
          </p>
        </div>

        {/* ── Right Column: Narasi Editor ── */}
        <div className="p-5 flex flex-col">
          <p className="uppercase text-xs tracking-wider text-text-muted font-semibold mb-1">
            NARASI VERBAL INDONESIA
          </p>
          <p className="text-xs text-text-muted mb-3">
            Teks ini akan menjadi{" "}
            <code className="bg-bg-page px-1 rounded text-[11px]">aria-label</code>{" "}
            rumus — dibacakan screen reader untuk siswa tunanetra.
          </p>

          <textarea
            aria-label={`Narasi verbal untuk rumus #${index}`}
            className="w-full min-h-[96px] border border-border-card rounded-lg p-4 text-sm resize-y focus:border-primary focus:ring-1 focus:ring-primary outline-none mb-3 transition-colors"
            value={currentNarration}
            onChange={(e) => onNarrationChange?.(e.target.value)}
            placeholder="Contoh: x pangkat dua ditambah satu"
            disabled={isApproved}
          />

          {/* Action buttons */}
          <div className="mt-auto flex gap-2">
            {/* Save button */}
            {onSave && !isApproved && (
              <button
                onClick={handleSave}
                disabled={saving}
                className={`flex-1 border rounded-lg py-2.5 text-sm font-medium transition-all ${
                  savedFlash
                    ? "bg-success/10 text-success border-success/30"
                    : "bg-white border-border-card text-text-secondary hover:border-primary hover:text-primary"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {saving ? (
                  <span className="flex items-center justify-center gap-1.5">
                    <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Menyimpan…
                  </span>
                ) : savedFlash ? (
                  "Tersimpan ✓"
                ) : (
                  "Simpan"
                )}
              </button>
            )}

            {/* Approve button */}
            <button
              onClick={onApprove}
              disabled={isApproved}
              aria-pressed={isApproved}
              className={`flex-1 border rounded-lg py-2.5 text-sm font-medium transition-colors ${
                isApproved
                  ? "bg-success text-white border-success cursor-default"
                  : "bg-white border-border-card text-text-primary hover:bg-primary hover:text-white hover:border-primary"
              } disabled:cursor-default`}
            >
              {isApproved ? "Telah Disetujui ✓" : "Setujui"}
            </button>
          </div>
        </div>
      </div>
    </article>
  );
};
