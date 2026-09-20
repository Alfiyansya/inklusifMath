/**
 * useNarrations — Fetches and manages narrations for a document.
 * Falls back to mock data when backend is unavailable.
 * Handles local edit state, API saves, and approval.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchDocumentNarrations,
  updateNarration as apiUpdateNarration,
  approveDocument as apiApproveDocument,
  type NarrationItem,
  type ApproveResult,
} from "@/lib/api/documents";

/** Narration with local UI state */
export interface NarrationWithState extends NarrationItem {
  /** Confidence score from AI (0-100) */
  aiConfidence: number;
  /** Whether this narration needs teacher attention */
  needsAttention: boolean;
  /** Whether teacher has approved this narration */
  isApproved: boolean;
  /** Local edit value (may differ from saved value) */
  localNarration: string;
  /** Whether a save is in progress */
  isSaving: boolean;
}

// ── Mock data matching current hardcoded values in review page ──
const MOCK_NARRATIONS: NarrationWithState[] = [
  {
    id: "1", originalNotation: "a/b", latex: "\\frac{a}{b}",
    aiNarration: "Pecahan. Pembilang: a. Penyebut: b.",
    teacherNarration: null, status: "ai_generated", positionOrder: 1,
    aiConfidence: 99, needsAttention: false, isApproved: false,
    localNarration: "Pecahan. Pembilang: a. Penyebut: b.", isSaving: false,
  },
  {
    id: "2", originalNotation: "1/(x+2)", latex: "\\frac{1}{x+2}",
    aiNarration: "Pecahan. Pembilang: angka satu. Penyebut: x ditambah dua. Catatan: penyebut merupakan satu kesatuan ekspresi.",
    teacherNarration: null, status: "ai_generated", positionOrder: 2,
    aiConfidence: 97, needsAttention: false, isApproved: false,
    localNarration: "Pecahan. Pembilang: angka satu. Penyebut: x ditambah dua. Catatan: penyebut merupakan satu kesatuan ekspresi.", isSaving: false,
  },
  {
    id: "3", originalNotation: "(3x-5)/2 = 8", latex: "\\frac{3x-5}{2} = 8",
    aiNarration: "Persamaan linear: pecahan dengan pembilang tiga dikali x dikurangi lima, dan penyebut angka dua, sama dengan delapan.",
    teacherNarration: null, status: "ai_generated", positionOrder: 3,
    aiConfidence: 99, needsAttention: false, isApproved: false,
    localNarration: "Persamaan linear: pecahan dengan pembilang tiga dikali x dikurangi lima, dan penyebut angka dua, sama dengan delapan.", isSaving: false,
  },
  {
    id: "4", originalNotation: "2³ × 2⁴ = 2⁷", latex: "2^{3} \\times 2^{4} = 2^{7}",
    aiNarration: "Persamaan perpangkatan: dua pangkat tiga, dikali dua pangkat empat, sama dengan dua pangkat tujuh.",
    teacherNarration: null, status: "ai_generated", positionOrder: 4,
    aiConfidence: 91, needsAttention: true, isApproved: false,
    localNarration: "Persamaan perpangkatan: dua pangkat tiga, dikali dua pangkat empat, sama dengan dua pangkat tujuh.", isSaving: false,
  },
];

interface UseNarrationsResult {
  narrations: NarrationWithState[];
  documentTitle: string;
  isLoading: boolean;
  error: string | null;
  isUsingMockData: boolean;
  remainingCount: number;
  /** Update local narration text (does NOT save to API) */
  editNarration: (id: string, value: string) => void;
  /** Save narration edit to API, then mark as reviewed */
  saveNarration: (id: string) => Promise<void>;
  /** Approve a single narration locally */
  approveNarration: (id: string) => void;
  /** Approve all and publish document — returns ApproveResult with moduleId */
  approveAll: () => Promise<ApproveResult | undefined>;
}

export function useNarrations(documentId: string): UseNarrationsResult {
  const [narrations, setNarrations] = useState<NarrationWithState[]>([]);
  const [documentTitle, setDocumentTitle] = useState("Dokumen");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUsingMockData, setIsUsingMockData] = useState(false);

  // Fetch narrations from API
  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const result = await fetchDocumentNarrations(documentId);
        setDocumentTitle(result.title);

        const mapped: NarrationWithState[] = result.expressions.map((e) => ({
          ...e,
          aiConfidence: 95, // Default — backend doesn't provide this yet
          needsAttention: false,
          isApproved: e.status === "approved",
          localNarration: e.teacherNarration ?? e.aiNarration ?? "",
          isSaving: false,
        }));

        setNarrations(mapped);
        setIsUsingMockData(false);
      } catch (err) {
        console.warn("[useNarrations] API gagal, fallback ke mock data:", err);
        setNarrations(MOCK_NARRATIONS);
        setDocumentTitle("Operasi_Bilangan.pdf");
        setIsUsingMockData(true);
        setError(err instanceof Error ? err.message : "Gagal memuat narasi");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [documentId]);

  // Edit narration locally (no API call)
  const editNarration = useCallback((id: string, value: string) => {
    setNarrations((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, localNarration: value, isApproved: false } : n,
      ),
    );
  }, []);

  // Save narration to API
  const saveNarration = useCallback(async (id: string) => {
    const narration = narrations.find((n) => n.id === id);
    if (!narration || isUsingMockData) return;

    setNarrations((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isSaving: true } : n)),
    );

    try {
      await apiUpdateNarration(id, narration.localNarration);
      setNarrations((prev) =>
        prev.map((n) =>
          n.id === id
            ? { ...n, teacherNarration: n.localNarration, status: "reviewed", isSaving: false }
            : n,
        ),
      );
    } catch (err) {
      console.warn("[useNarrations] Gagal menyimpan narasi:", err);
      setNarrations((prev) =>
        prev.map((n) => (n.id === id ? { ...n, isSaving: false } : n)),
      );
    }
  }, [narrations, isUsingMockData]);

  // Approve a single narration locally
  const approveNarration = useCallback((id: string) => {
    setNarrations((prev) =>
      prev.map((n) => (n.id === id ? { ...n, isApproved: true } : n)),
    );
  }, []);

  // Approve all narrations and publish — returns ApproveResult for redirect
  const approveAll = useCallback(async (): Promise<ApproveResult | undefined> => {
    if (isUsingMockData) {
      setNarrations((prev) => prev.map((n) => ({ ...n, isApproved: true })));
      return undefined;
    }

    try {
      const result = await apiApproveDocument(documentId);
      setNarrations((prev) => prev.map((n) => ({ ...n, isApproved: true })));
      return result;
    } catch (err) {
      console.warn("[useNarrations] Gagal menyetujui dokumen:", err);
      return undefined;
    }
  }, [documentId, isUsingMockData]);

  const remainingCount = narrations.filter((n) => !n.isApproved).length;

  return {
    narrations,
    documentTitle,
    isLoading,
    error,
    isUsingMockData,
    remainingCount,
    editNarration,
    saveNarration,
    approveNarration,
    approveAll,
  };
}
