/**
 * useGlobalShortcut — Registers a global keyboard shortcut.
 * Used for Alt+T tutor shortcut (FR-11).
 */

import { useEffect, useCallback } from 'react';

interface ShortcutOptions {
  key: string;
  altKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  onTrigger: () => void;
  enabled?: boolean;
}

export function useGlobalShortcut({
  key,
  altKey = false,
  ctrlKey = false,
  shiftKey = false,
  onTrigger,
  enabled = true,
}: ShortcutOptions) {
  const handler = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const matchesKey = event.key.toLowerCase() === key.toLowerCase();
      const matchesAlt = event.altKey === altKey;
      const matchesCtrl = event.ctrlKey === ctrlKey;
      const matchesShift = event.shiftKey === shiftKey;

      if (matchesKey && matchesAlt && matchesCtrl && matchesShift) {
        event.preventDefault();
        event.stopPropagation();
        onTrigger();
      }
    },
    [key, altKey, ctrlKey, shiftKey, onTrigger, enabled],
  );

  useEffect(() => {
    if (!enabled) return;
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [handler, enabled]);
}
