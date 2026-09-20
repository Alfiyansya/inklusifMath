"use client";

/**
 * useMathJax — lazy-loads MathJax 3 script and exposes a typeset function.
 *
 * Why MathJax 3 instead of 4?
 *   package.json has "mathjax-full": "^3.2.1". MathJax 4 is still pre-release.
 *   We use the CDN script tag approach so Next.js doesn't try to bundle MathJax
 *   (it's 150KB+ and server-side bundling breaks due to browser-only DOM APIs).
 *
 * Usage:
 *   const { typeset } = useMathJax();
 *   // call typeset(element) after inserting new LaTeX into the DOM
 */

import { useEffect, useRef, useCallback } from "react";

const MATHJAX_CDN =
  "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js";

// Configure MathJax before the script loads.
// This must be on window before the MathJax script tag runs.
const MATHJAX_CONFIG = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    packages: { "[+]": ["base", "ams", "newcommand"] },
  },
  options: {
    // Disable MathJax's own speech output — we provide aria-label from narasi guru.
    enableAssistiveMml: false,
    menuOptions: {
      settings: {
        assistiveMml: false,
      },
    },
  },
  chtml: {
    scale: 1.1,
    mathmlSpacing: true,
  },
  startup: {
    typeset: false, // We control when typeset runs
  },
};

let scriptLoaded = false;
let scriptLoading = false;
const readyCallbacks: Array<() => void> = [];

function loadMathJaxScript(onReady: () => void): void {
  if (scriptLoaded) {
    onReady();
    return;
  }
  readyCallbacks.push(onReady);
  if (scriptLoading) return;

  scriptLoading = true;

  // Inject config before script
  if (typeof window !== "undefined") {
    (window as unknown as Record<string, unknown>).MathJax = MATHJAX_CONFIG;
  }

  const script = document.createElement("script");
  script.id = "mathjax-cdn";
  script.src = MATHJAX_CDN;
  script.async = true;
  script.onload = () => {
    scriptLoaded = true;
    readyCallbacks.forEach((cb) => cb());
    readyCallbacks.length = 0;
  };
  script.onerror = () => {
    scriptLoading = false; // allow retry on next mount
  };
  document.head.appendChild(script);
}

export interface UseMathJaxReturn {
  /** Call after inserting new LaTeX into the DOM to trigger rendering. */
  typeset: (element?: HTMLElement | null) => Promise<void>;
  /** True once MathJax script has loaded. */
  isLoaded: boolean;
}

export function useMathJax(): UseMathJaxReturn {
  const isLoadedRef = useRef(false);

  useEffect(() => {
    loadMathJaxScript(() => {
      isLoadedRef.current = true;
    });
  }, []);

  const typeset = useCallback(async (element?: HTMLElement | null) => {
    if (typeof window === "undefined") return;
    const mj = (window as unknown as Record<string, unknown>).MathJax as
      | { typesetPromise?: (nodes?: HTMLElement[]) => Promise<void> }
      | undefined;

    if (!mj?.typesetPromise) return;

    try {
      if (element) {
        await mj.typesetPromise([element]);
      } else {
        await mj.typesetPromise();
      }
    } catch {
      // MathJax typeset errors are non-fatal — render falls back to LaTeX text
    }
  }, []);

  return { typeset, isLoaded: isLoadedRef.current };
}
