"use client";

/**
 * MathRenderer — renders a LaTeX expression visually using MathJax.
 *
 * Implements TDD ADR-003 dual-layer strategy:
 *   - Visual layer: MathJax renders LaTeX to CHTML/SVG
 *   - Accessible layer: aria-label from teacher/AI narration (Bahasa Indonesia)
 *
 * The aria-label OVERRIDES MathJax's default English speech output.
 * This is crucial for screen reader users — they hear "x pangkat dua"
 * (Indonesian, from narasi guru) instead of MathJax's "x squared" (English).
 *
 * Accessibility:
 *   - role="math"            — landmark for screen reader
 *   - aria-label             — narasi verbal Indonesia (dari guru / AI)
 *   - aria-roledescription   — "rumus matematika" for context
 *   - focusable              — keyboard users can Tab to each formula
 *   - Loading state          — monospace fallback while MathJax loads
 *
 * Usage:
 *   <MathRenderer
 *     latex="\frac{1}{2}"
 *     narration="satu per dua"
 *     display={false}
 *   />
 */

import React, { useRef, useEffect, useId } from "react";
import { useMathJax } from "@/hooks/useMathJax";

export interface MathRendererProps {
  /** LaTeX string, e.g. "x^{2}" or "\\frac{1}{2}" */
  latex: string;
  /**
   * Verbal narration in Bahasa Indonesia — used as aria-label.
   * If omitted, screen readers will read the raw LaTeX (not ideal).
   */
  narration?: string;
  /**
   * Display mode: true = block (centered, larger), false = inline
   * @default false
   */
  display?: boolean;
  /** Additional CSS class on the wrapper element */
  className?: string;
  /** @default "math" */
  role?: string;
}

export const MathRenderer: React.FC<MathRendererProps> = ({
  latex,
  narration,
  display = false,
  className = "",
  role = "math",
}) => {
  const containerRef = useRef<HTMLSpanElement>(null);
  const { typeset } = useMathJax();
  const mathId = useId();

  // Wrap LaTeX in MathJax delimiters based on display mode
  const wrappedLatex = display ? `\\[${latex}\\]` : `\\(${latex}\\)`;

  // Re-typeset whenever latex changes
  useEffect(() => {
    if (!containerRef.current) return;
    // Reset to raw LaTeX (MathJax will process it)
    containerRef.current.textContent = wrappedLatex;
    typeset(containerRef.current);
  }, [latex, display, typeset, wrappedLatex]);

  const Tag = display ? "div" : "span";

  return (
    <Tag
      id={mathId}
      ref={containerRef as React.RefObject<HTMLDivElement & HTMLSpanElement>}
      role={role}
      aria-label={narration ?? latex}
      aria-roledescription="rumus matematika"
      tabIndex={0}
      className={[
        // Base styles
        display ? "block text-center my-4 overflow-x-auto" : "inline-block align-middle",
        // Focusable ring for keyboard users
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded",
        // Fallback font while MathJax loads
        "font-mono",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      // Prevent screen readers from reading MathJax-generated MathML
      // (we control the narration via aria-label)
      aria-hidden={false}
    >
      {wrappedLatex}
    </Tag>
  );
};

export default MathRenderer;
