/**
 * LiveRegion — Announces dynamic content to screen readers.
 * Used for tutor responses (FR-15) and error messages.
 *
 * Uses aria-live to let the screen reader announce content
 * without disrupting the user's current focus position.
 */

'use client';

import { useEffect, useRef } from 'react';

interface LiveRegionProps {
  /** The message to announce. Changing this triggers a new announcement. */
  message: string;
  /** 'polite' waits for screen reader to finish; 'assertive' interrupts immediately. */
  politeness?: 'polite' | 'assertive';
  /** Additional CSS classes */
  className?: string;
  /** If true, the region content is visually visible (not just for screen readers) */
  visible?: boolean;
}

export function LiveRegion({
  message,
  politeness = 'polite',
  className = '',
  visible = false,
}: LiveRegionProps) {
  const regionRef = useRef<HTMLDivElement>(null);

  // Clear and re-set to ensure screen reader re-announces
  useEffect(() => {
    const el = regionRef.current;
    if (!el || !message) return;

    el.textContent = '';
    // Force reflow so screen reader sees the change
    void el.offsetHeight;
    el.textContent = message;
  }, [message]);

  const visuallyHiddenStyle = visible
    ? {}
    : {
        position: 'absolute' as const,
        width: '1px',
        height: '1px',
        padding: '0',
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap' as const,
        border: '0',
      };

  return (
    <div
      ref={regionRef}
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className={className}
      style={visuallyHiddenStyle}
    />
  );
}
