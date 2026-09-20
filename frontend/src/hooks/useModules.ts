/**
 * useModules — Fetches published modules from the API.
 * Falls back to mock data when backend is unavailable (e.g., 501, network error).
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchModules } from "@/lib/api/modules";

/** Enriched module type matching what dashboard pages need */
export interface DashboardModule {
  id: string;
  title: string;
  category: string;
  grade: string;
  teacher: string;
  features: string[];
  status: "published" | "draft" | "review";
  publishedAt: string | null;
  /** Estimated reading time for student view */
  readingTime: string;
}

// ── Mock data matching current hardcoded values in dashboard pages ──
const MOCK_MODULES: DashboardModule[] = [
  { id: "1", title: "Operasi Bilangan Bulat", category: "MATEMATIKA SD", grade: "Kelas 4 SD", teacher: "Bu Sari Dewi", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-01", readingTime: "~15 mnt" },
  { id: "2", title: "Operasi Bilangan Pecahan", category: "MATEMATIKA SD", grade: "Kelas 5 SD", teacher: "Bu Sari Dewi", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-02", readingTime: "~20 mnt" },
  { id: "3", title: "KPK dan FPB", category: "MATEMATIKA SD", grade: "Kelas 5 SD", teacher: "Pak Rudi Hartono", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-03", readingTime: "~18 mnt" },
  { id: "4", title: "Perkalian dan Pembagian", category: "MATEMATIKA SD", grade: "Kelas 4 SD", teacher: "Bu Sari Dewi", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-04", readingTime: "~12 mnt" },
  { id: "5", title: "Pengantar Persamaan Linear", category: "ALJABAR SMP", grade: "Kelas 7 SMP", teacher: "Pak Budi Santoso", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-05", readingTime: "~25 mnt" },
  { id: "6", title: "Rasio dan Proporsi", category: "MATEMATIKA SMP", grade: "Kelas 7 SMP", teacher: "Bu Ani Rahayu", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-06", readingTime: "~20 mnt" },
  { id: "7", title: "Bilangan Bulat Negatif", category: "MATEMATIKA SMP", grade: "Kelas 7 SMP", teacher: "Pak Budi Santoso", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-07", readingTime: "~15 mnt" },
  { id: "8", title: "Persentase dan Desimal", category: "MATEMATIKA SMP", grade: "Kelas 8 SMP", teacher: "Bu Ani Rahayu", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published", publishedAt: "2026-09-08", readingTime: "~18 mnt" },
];

interface UseModulesResult {
  modules: DashboardModule[];
  isLoading: boolean;
  error: string | null;
  isUsingMockData: boolean;
  refetch: () => void;
}

export function useModules(): UseModulesResult {
  const [modules, setModules] = useState<DashboardModule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUsingMockData, setIsUsingMockData] = useState(false);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const apiModules = await fetchModules();

      // Map API data to enriched dashboard format
      const mapped: DashboardModule[] = apiModules.map((m) => ({
        id: m.id,
        title: m.title,
        category: "MATEMATIKA",
        grade: "",
        teacher: "",
        features: ["Keyboard navigasi", "Rumus naratif"],
        status: "published" as const,
        publishedAt: m.publishedAt,
        readingTime: "~15 mnt",
      }));

      setModules(mapped);
      setIsUsingMockData(false);
    } catch (err) {
      console.warn("[useModules] API gagal, fallback ke mock data:", err);
      setModules(MOCK_MODULES);
      setIsUsingMockData(true);
      setError(err instanceof Error ? err.message : "Gagal memuat modul");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { modules, isLoading, error, isUsingMockData, refetch: fetchData };
}
