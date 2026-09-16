/**
 * useFocusRestore — Saves the currently focused element and restores it later.
 * Critical for tutor dialog (FR-12, FR-16): preserves reading position
 * when modal opens/closes.
 */

import { useRef, useCallback } from 'react';

export function useFocusRestore() {
  const savedElement = useRef<HTMLElement | null>(null);

  const saveFocus = useCallback(() => {
    savedElement.current = document.activeElement as HTMLElement | null;
  }, []);

  const restoreFocus = useCallback(() => {
    if (savedElement.current && typeof savedElement.current.focus === 'function') {
      // Small delay to ensure DOM has settled after modal close
      requestAnimationFrame(() => {
        savedElement.current?.focus();
        savedElement.current = null;
      });
    }
  }, []);

  return { saveFocus, restoreFocus };
}
