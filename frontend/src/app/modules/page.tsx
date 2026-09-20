"use client";

/**
 * /modules — Daftar semua modul yang sudah dipublikasikan.
 *
 * Ini adalah halaman SISWA untuk browse modul.
 * Berbeda dengan /dashboard/student yang lebih personal (progress, topik, sapaan).
 *
 * Aksesibilitas:
 *   - Skip link ke #module-list
 *   - Setiap kartu = <article> dengan aria-label
 *   - "Mulai Belajar" dengan aria-describedby ke judul modul
 *   - Empty state dengan aria-live
 *   - Skeleton loading dengan aria-busy
 */

import Link from "next/link";
import { ApiStatusBanner } from "@/components/ui/ApiStatusBanner";
import { useModules } from "@/hooks/useModules";

export default function ModulesPage() {
  const { modules, isLoading, isUsingMockData } = useModules();

  return (
    <div className="min-h-screen bg-bg-page">
      {/* Skip link for keyboard users */}
      <a
        href="#module-list"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-white px-4 py-2 rounded-lg z-50 text-sm font-medium"
      >
        Langsung ke daftar modul
      </a>

      {/* Page header */}
      <header className="bg-white border-b border-border-card px-4 sm:px-8 py-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard/student"
            className="text-text-secondary hover:text-primary transition-colors text-sm font-medium"
          >
            &larr; Beranda Siswa
          </Link>
          <div className="h-4 w-px bg-border-card" aria-hidden="true" />
          <span className="font-semibold text-text-primary">Daftar Modul</span>
        </div>
        <span className="text-xs text-text-muted font-medium uppercase tracking-wider">
          InklusifMath
        </span>
      </header>

      <main className="container max-w-[1152px] mx-auto px-4 sm:px-8 py-6 sm:py-10" id="main-content">
        {/* Page title */}
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-text-primary">
            Modul Belajar Matematika
          </h1>
          <p className="text-text-secondary mt-1 text-sm">
            Setiap modul dilengkapi narasi verbal dan dapat diakses dengan screen reader.
            Gunakan <kbd className="bg-bg-page border border-border-card rounded px-1.5 py-0.5 text-xs font-mono">Tab</kbd> untuk navigasi.
          </p>
        </div>

        {isUsingMockData && (
          <div className="mb-6">
            <ApiStatusBanner context="Daftar modul menggunakan data contoh — backend tidak tersedia" />
          </div>
        )}

        {/* Module grid */}
        {isLoading ? (
          <div
            className="grid grid-cols-1 sm:grid-cols-2 gap-6"
            aria-busy="true"
            aria-label="Memuat daftar modul…"
          >
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white rounded-2xl h-52 animate-pulse"
                style={{ border: "0.8px solid var(--color-border-card)" }}
              />
            ))}
          </div>
        ) : modules.length === 0 ? (
          <div
            role="status"
            aria-live="polite"
            className="text-center py-20 rounded-2xl"
            style={{ border: "0.8px solid var(--color-border-card)", color: "var(--color-text-muted)" }}
          >
            <p className="text-2xl mb-2">📚</p>
            <p className="text-lg font-medium">Belum ada modul tersedia.</p>
            <p className="text-sm mt-1">Guru sedang menyiapkan materi. Cek kembali nanti.</p>
          </div>
        ) : (
          <ul
            id="module-list"
            className="grid grid-cols-1 sm:grid-cols-2 gap-6"
            aria-label={`${modules.length} modul tersedia`}
          >
            {modules.map((mod) => (
              <li key={mod.id}>
                <ModuleCard module={mod} />
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}

// ── Module Card ────────────────────────────────────────────────────────────────

interface ModuleCardProps {
  module: {
    id: string;
    title: string;
    grade: string;
    teacher: string;
    readingTime: string;
    publishedAt: string | null;
  };
}

function ModuleCard({ module: mod }: ModuleCardProps) {
  const cardId = `module-title-${mod.id}`;
  const publishDate = mod.publishedAt
    ? new Date(mod.publishedAt).toLocaleDateString("id-ID", {
        day: "numeric", month: "long", year: "numeric",
      })
    : null;

  return (
    <article
      aria-labelledby={cardId}
      className="bg-white rounded-2xl overflow-hidden flex flex-col transition-shadow hover:shadow-sm focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2"
      style={{ border: "0.8px solid var(--color-border-card)" }}
    >
      {/* Card top accent */}
      <div className="h-1 bg-primary" aria-hidden="true" />

      <div className="p-6 flex flex-col flex-1">
        {/* Meta */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          {mod.grade && (
            <span
              className="text-xs font-bold px-2.5 py-1 rounded-full"
              style={{
                backgroundColor: "rgba(100, 149, 237, 0.15)",
                color: "var(--color-primary)",
              }}
            >
              {mod.grade}
            </span>
          )}
          <span className="text-xs text-text-muted">{mod.readingTime}</span>
          {publishDate && (
            <span className="text-xs text-text-muted ml-auto">
              Diterbitkan {publishDate}
            </span>
          )}
        </div>

        {/* Title */}
        <h2
          id={cardId}
          className="text-lg font-bold text-text-primary mb-1 line-clamp-2"
        >
          {mod.title}
        </h2>
        {mod.teacher && (
          <p className="text-sm text-text-secondary mb-4">Oleh {mod.teacher}</p>
        )}

        {/* Feature badges */}
        <div className="flex gap-2 flex-wrap mb-5" aria-label="Fitur aksesibilitas">
          <AccessBadge>Narasi Verbal</AccessBadge>
          <AccessBadge>Screen Reader</AccessBadge>
          <AccessBadge>Keyboard</AccessBadge>
        </div>

        {/* CTA */}
        <div className="mt-auto">
          <Link
            href={`/modules/${mod.id}`}
            aria-describedby={cardId}
            className="block w-full py-3 rounded-xl font-bold text-sm text-white text-center transition-colors hover:opacity-90 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            Mulai Belajar
          </Link>
        </div>
      </div>
    </article>
  );
}

function AccessBadge({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="text-xs px-2 py-0.5 rounded-full font-medium"
      style={{
        backgroundColor: "rgba(100, 149, 237, 0.08)",
        color: "var(--color-text-secondary)",
        border: "0.8px solid var(--color-border-card)",
      }}
    >
      {children}
    </span>
  );
}
