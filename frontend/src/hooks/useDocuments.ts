/**
 * useDocuments — fetches the authenticated teacher's document list.
 *
 * Returns:
 *   documents: DocumentListItem[]  — list from GET /documents
 *   total: number                  — total count for pagination
 *   isLoading: boolean
 *   error: string | null
 *   isUsingMockData: boolean       — true when backend is unreachable
 *   refetch: () => void            — manual refresh trigger
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchDocumentList, type DocumentListItem } from "@/lib/api/documents";

// ── Mock fallback data ────────────────────────────────────────────────────────

const MOCK_DOCUMENTS: DocumentListItem[] = [
  {
    documentId: "mock-1",
    title: "Aljabar Linear (Contoh)",
    fileType: "docx",
    parsingStatus: "parsed",
    ocrUsed: "none",
    mathExpressionsCount: 5,
    isPublished: true,
    moduleId: "mock-module-1",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    documentId: "mock-2",
    title: "Kalkulus Integral (Contoh)",
    fileType: "pdf",
    parsingStatus: "processing",
    ocrUsed: "pending_ocr",
    mathExpressionsCount: 0,
    isPublished: false,
    moduleId: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

// ── Hook ──────────────────────────────────────────────────────────────────────

interface UseDocumentsResult {
  documents: DocumentListItem[];
  total: number;
  isLoading: boolean;
  error: string | null;
  isUsingMockData: boolean;
  refetch: () => void;
}

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUsingMockData, setIsUsingMockData] = useState(false);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchDocumentList();
      setDocuments(result.documents);
      setTotal(result.total);
      setIsUsingMockData(false);
    } catch (err) {
      console.warn("[useDocuments] API gagal, fallback ke mock data:", err);
      setDocuments(MOCK_DOCUMENTS);
      setTotal(MOCK_DOCUMENTS.length);
      setIsUsingMockData(true);
      setError(err instanceof Error ? err.message : "Gagal memuat dokumen");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { documents, total, isLoading, error, isUsingMockData, refetch: fetchData };
}
