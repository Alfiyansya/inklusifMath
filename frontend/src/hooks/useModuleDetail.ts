"use client";

/**
 * useModuleDetail — Fetches a single module's content and math expressions.
 * Falls back to mock data when backend is unavailable.
 */

import { useState, useEffect } from "react";
import { fetchModuleDetail, type ModuleDetail } from "@/lib/api/modules";

// ── Mock module detail (for offline/dev mode) ──────────────────────────────

const MOCK_MODULE: ModuleDetail = {
  id: "mock",
  title: "Operasi Bilangan Bulat (Contoh)",
  htmlContent: `
    <section>
      <h2>Pendahuluan</h2>
      <p>Bilangan bulat adalah bilangan yang tidak memiliki bagian pecahan.
         Bilangan bulat terdiri dari bilangan positif, nol, dan bilangan negatif.</p>
    </section>
    <section>
      <h2>Penjumlahan Bilangan Bulat</h2>
      <p>Penjumlahan bilangan bulat positif sama seperti penjumlahan biasa.</p>
      <p>Contoh: tiga ditambah empat sama dengan tujuh.</p>
    </section>
    <section>
      <h2>Pengurangan Bilangan Bulat</h2>
      <p>Pengurangan bilangan bulat mengikuti aturan tanda.</p>
      <p>Contoh: lima dikurangi negatif dua sama dengan tujuh.</p>
    </section>
  `,
  mathExpressions: [
    {
      id: "m1", originalNotation: "3 + 4 = 7",
      latex: "3 + 4 = 7",
      aiNarration: "tiga ditambah empat sama dengan tujuh",
      teacherNarration: "tiga ditambah empat sama dengan tujuh",
      status: "approved", positionOrder: 1,
    },
    {
      id: "m2", originalNotation: "5 - (-2) = 7",
      latex: "5 - (-2) = 7",
      aiNarration: "lima dikurangi negatif dua sama dengan tujuh",
      teacherNarration: null,
      status: "ai_generated", positionOrder: 2,
    },
  ],
};

interface UseModuleDetailResult {
  module: ModuleDetail | null;
  isLoading: boolean;
  error: string | null;
  isUsingMockData: boolean;
}

export function useModuleDetail(moduleId: string): UseModuleDetailResult {
  const [module, setModule] = useState<ModuleDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUsingMockData, setIsUsingMockData] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await fetchModuleDetail(moduleId);
        if (!cancelled) {
          setModule(data);
          setIsUsingMockData(false);
        }
      } catch (err) {
        if (!cancelled) {
          console.warn("[useModuleDetail] API gagal, fallback ke mock:", err);
          setModule({ ...MOCK_MODULE, id: moduleId });
          setIsUsingMockData(true);
          setError(err instanceof Error ? err.message : "Gagal memuat modul");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [moduleId]);

  return { module, isLoading, error, isUsingMockData };
}
