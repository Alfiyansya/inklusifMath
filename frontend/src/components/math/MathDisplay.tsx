"use client";

/**
 * MathDisplay — dual-layer math component for the student module reader.
 *
 * Combines:
 *   1. Visual layer: MathRenderer (MathJax) for sighted users
 *   2. Semantic layer: aria-label with teacher-verified narasi verbal Indonesia
 *      for screen reader users (blind/low-vision students)
 *
 * This is the component to use on student-facing module pages (/modules/[id]).
 * For the teacher review UI, use MathRenderer directly (NarrationCard).
 *
 * Accessibility guarantees:
 *   - aria-label always present (falls back to AI narration → LaTeX)
 *   - role="math" + aria-roledescription="rumus matematika"
 *   - Focusable via Tab key
 *   - High-contrast visual outline on focus
 *   - Live region announce optional (for dynamic content)
 *
 * Usage:
 *   <MathDisplay
 *     latex="x^{2} + 1"
 *     teacherNarration="x pangkat dua ditambah satu"
 *     aiNarration="x pangkat dua ditambah satu"
 *     display={false}
 *   />
 */

import React from "react";
import { MathRenderer } from "./MathRenderer";

export interface MathDisplayProps {
  /** LaTeX string */
  latex: string;
  /** Teacher-verified narration — highest priority for aria-label */
  teacherNarration?: string | null;
  /** AI-generated narration — used if no teacher narration */
  aiNarration?: string | null;
  /**
   * Display mode: block (centered) vs inline
   * @default false
   */
  display?: boolean;
  /** Additional class on the wrapper */
  className?: string;
  /**
   * If true, wrap in a <figure> with <figcaption> showing the narration text.
   * Useful for accessibility audits and teacher review.
   * @default false
   */
  showCaption?: boolean;
}

export const MathDisplay: React.FC<MathDisplayProps> = ({
  latex,
  teacherNarration,
  aiNarration,
  display = false,
  className = "",
  showCaption = false,
}) => {
  // Priority: teacher narration > AI narration > raw LaTeX
  const narration = teacherNarration ?? aiNarration ?? latex;

  const mathEl = (
    <MathRenderer
      latex={latex}
      narration={narration}
      display={display}
      className={className}
    />
  );

  if (!showCaption) {
    return mathEl;
  }

  // With caption (for teacher review / accessibility audit mode)
  return (
    <figure className={display ? "my-4" : "inline"}>
      {mathEl}
      <figcaption
        className={[
          "text-sm text-text-secondary mt-1 italic",
          display ? "text-center" : "inline ml-2",
        ].join(" ")}
        aria-hidden="true" // Caption is decorative — aria-label on math element is canonical
      >
        {narration}
      </figcaption>
    </figure>
  );
};

export default MathDisplay;
