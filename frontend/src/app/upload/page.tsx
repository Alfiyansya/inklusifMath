"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UploadZone } from "@/components/teacher/UploadZone";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setIsUploading(true);
    setStatusMessage("Mengunggah berkas...");
    
    // Simulate upload progress
    let currentProgress = 0;
    const interval = setInterval(() => {
      currentProgress += 10;
      setProgress(currentProgress);
      
      if (currentProgress === 50) {
        setStatusMessage("Menganalisis konten...");
      } else if (currentProgress === 80) {
        setStatusMessage("Mengekstrak rumus matematika...");
      }
      
      if (currentProgress >= 100) {
        clearInterval(interval);
        setStatusMessage("Selesai!");
        setTimeout(() => {
          router.push(`/upload/123/review`);
        }, 500);
      }
    }, 400);
  };

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
        
        <UploadZone
          onFileSelect={handleFileSelect}
          isUploading={isUploading}
          progress={progress}
          fileName={file?.name}
          statusMessage={statusMessage}
        />
      </main>
    </div>
  );
}
