/**
 * useDocumentUpload — Handles document upload via API.
 * Falls back to simulated progress when backend returns 501.
 */

"use client";

import { useState, useCallback } from "react";
import { uploadDocument } from "@/lib/api/documents";

interface UseDocumentUploadResult {
  /** Trigger the upload process */
  upload: (file: File) => void;
  /** Whether an upload is in progress */
  isUploading: boolean;
  /** Upload progress 0-100 */
  progress: number;
  /** Human-readable status message */
  statusMessage: string;
  /** The uploaded document ID (from API response) */
  documentId: string | null;
  /** Error message if upload failed */
  error: string | null;
  /** Whether the upload is using simulation (backend not ready) */
  isSimulated: boolean;
}

export function useDocumentUpload(): UseDocumentUploadResult {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSimulated, setIsSimulated] = useState(false);

  const simulateUpload = useCallback((fileName: string) => {
    // Fallback: simulate progress like the original implementation
    setIsSimulated(true);
    let currentProgress = 0;

    const interval = setInterval(() => {
      currentProgress += 10;
      setProgress(currentProgress);

      if (currentProgress === 30) {
        setStatusMessage("Mengunggah berkas...");
      } else if (currentProgress === 50) {
        setStatusMessage("Menganalisis konten...");
      } else if (currentProgress === 80) {
        setStatusMessage("Mengekstrak rumus matematika...");
      }

      if (currentProgress >= 100) {
        clearInterval(interval);
        setStatusMessage("Selesai!");
        // Use a fake document ID for simulation
        setDocumentId("mock-" + Date.now());
      }
    }, 400);
  }, []);

  const upload = useCallback(
    (file: File) => {
      setIsUploading(true);
      setProgress(0);
      setError(null);
      setDocumentId(null);
      setIsSimulated(false);
      setStatusMessage("Mengunggah berkas...");

      // Extract title from filename (remove extension)
      const title = file.name.replace(/\.(docx|pdf)$/i, "");

      uploadDocument(file, title)
        .then((result) => {
          // Real API success
          setProgress(100);
          setStatusMessage("Selesai!");
          setDocumentId(result.documentId);
        })
        .catch((err) => {
          // API failed (501, network error, etc.) — fallback to simulation
          console.warn(
            "[useDocumentUpload] API gagal, fallback ke simulasi:",
            err,
          );
          setError(err instanceof Error ? err.message : "Upload gagal");
          simulateUpload(file.name);
        });
    },
    [simulateUpload],
  );

  return {
    upload,
    isUploading,
    progress,
    statusMessage,
    documentId,
    error,
    isSimulated,
  };
}
