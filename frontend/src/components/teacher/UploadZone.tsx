"use client";

import React, { useRef } from "react";

interface UploadZoneProps {
  onFileSelect?: (file: File) => void;
  isUploading?: boolean;
  progress?: number; // 0-100
  fileName?: string;
  statusMessage?: string;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFileSelect,
  isUploading = false,
  progress = 0,
  fileName,
  statusMessage,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onFileSelect) {
      onFileSelect(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (isUploading) return;
    
    const file = e.dataTransfer.files?.[0];
    if (file && onFileSelect) {
      onFileSelect(file);
    }
  };

  if (isUploading) {
    return (
      <div 
        className="border-2 border-border-card rounded-xl p-12 bg-white flex flex-col items-center justify-center"
        aria-live="polite"
      >
        <p className="font-medium text-lg mb-6">{fileName}</p>
        <div className="w-full max-w-md h-3 bg-bg-page rounded-full overflow-hidden mb-4">
          <div 
            className="h-full bg-primary transition-all duration-300 ease-in-out" 
            style={{ width: `${progress}%` }} 
          />
        </div>
        <p className="text-xl font-bold text-primary mb-2">{Math.round(progress)}%</p>
        {statusMessage && <p className="text-sm text-text-secondary">{statusMessage}</p>}
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Pilih dokumen DOCX atau PDF untuk diunggah"
      onClick={handleClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleClick();
        }
      }}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className="border-2 border-dashed border-border-card rounded-xl p-6 sm:p-12 text-center cursor-pointer hover:border-primary transition-colors flex flex-col items-center justify-center bg-bg-card focus-visible:ring-2 focus-visible:ring-primary"
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".docx,.pdf"
      />
      <div className="w-16 h-16 rounded-full bg-bg-page flex items-center justify-center mb-4 text-text-muted">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
        </svg>
      </div>
      <p className="text-lg font-medium text-text-primary mb-2">Seret berkas ke sini atau klik untuk memilih</p>
      <p className="text-sm text-text-muted">.docx, .pdf</p>
    </div>
  );
};
