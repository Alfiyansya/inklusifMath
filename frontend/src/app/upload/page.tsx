"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UploadZone } from "@/components/teacher/UploadZone";
import { ApiStatusBanner } from "@/components/ui/ApiStatusBanner";
import { useDocumentUpload } from "@/hooks/useDocumentUpload";

export default function UploadPage() {
  const router = useRouter();
  const {
    upload,
    isUploading,
    progress,
    statusMessage,
    documentId,
    isSimulated,
  } = useDocumentUpload();

  const handleFileSelect = (file: File) => {
    upload(file);
  };

  // Navigate to review page when upload completes
  useEffect(() => {
    if (documentId && progress >= 100) {
      const timer = setTimeout(() => {
        router.push(`/upload/${documentId}/review`);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [documentId, progress, router]);

  return (
    <div className="min-h-screen bg-bg-page">
      {/* Header */}
      <header className="bg-white border-b border-border-card px-8 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-text-secondary hover:text-primary transition-colors text-sm font-medium">
            &larr; Beranda
          </Link>
          <div className="h-4 w-px bg-border-card" />
          <span className="font-semibold text-text-primary">Portal Guru &mdash; Unggah Modul</span>
        </div>
        <span className="text-xs text-text-muted font-medium uppercase tracking-wider">InklusifMath Platform</span>
      </header>

      {/* Main Content */}
      <main className="container max-w-[1152px] mx-auto px-8 py-8">
        <h2 className="text-2xl font-bold mb-4 text-text-primary">Unggah Materi Ajar</h2>
        <p className="text-text-secondary mb-8 max-w-2xl">
          Sistem AI akan secara otomatis memproses dokumen Anda, mengekstrak semua rumus matematika, dan menghasilkan narasi verbal bahasa Indonesia yang inklusif untuk aksesibilitas pembaca layar (screen reader).
        </p>

        {isSimulated && (
          <ApiStatusBanner context="Proses upload menggunakan simulasi" />
        )}

        <UploadZone
          onFileSelect={handleFileSelect}
          isUploading={isUploading}
          progress={progress}
          fileName={undefined}
          statusMessage={statusMessage}
        />
      </main>
    </div>
  );
}
