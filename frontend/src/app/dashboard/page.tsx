"use client";

import Link from "next/link";
import { FeatureList } from "@/components/ui/FeatureList";
import { StatCard } from "@/components/ui/StatCard";
import { ModuleCard } from "@/components/ui/ModuleCard";
import { KeyboardShortcuts } from "@/components/ui/KeyboardShortcuts";
import { ApiStatusBanner } from "@/components/ui/ApiStatusBanner";
import { useModules } from "@/hooks/useModules";
import { useDocuments } from "@/hooks/useDocuments";

export default function TeacherDashboard() {
  const { modules, isLoading: modulesLoading, isUsingMockData: modulesUsingMock } = useModules();
  const { documents, total: docsTotal, isLoading: docsLoading, isUsingMockData: docsUsingMock } = useDocuments();

  return (
    <div className="max-w-[1152px] mx-auto px-8">
      {/* Hero Section */}
      <section className="py-10">
        <div className="grid grid-cols-2 gap-16 items-start">
          <div>
            <h1 className="text-5xl font-bold leading-tight" style={{ color: "var(--color-text-primary)" }}>
              Belajar Matematika<br />
              <span style={{ color: "var(--color-primary)" }}>Tanpa Hambatan</span>
            </h1>
            <p className="text-lg leading-relaxed mt-4" style={{ color: "var(--color-text-secondary)" }}>
              Platform e-learning inklusif untuk siswa tunanetra dan guru
              matematika. Materi dibaca oleh screen reader bawaan Anda
              — tanpa suara web yang mengganggu, tanpa ambiguitas rumus.
            </p>
            <Link
              href="/upload"
              className="px-6 py-3 rounded-xl font-bold text-sm text-white mt-8 inline-block transition-colors"
              style={{ backgroundColor: "var(--color-primary)" }}
            >
              Unggah Modul →
            </Link>
          </div>
          <div>
            <FeatureList />
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-6">
        <div className="grid grid-cols-4 gap-4">
          <StatCard value={String(docsTotal || modules.length)} label="Modul Tersedia" />
          <StatCard value="8" label="Guru Aktif" />
          <StatCard value="137" label="Siswa Terdaftar" />
          <StatCard value="100%" label="Kepatuhan WCAG" />
        </div>
      </section>

      {/* My Documents Section */}
      <section className="py-8" aria-labelledby="dokumen-saya-heading">
        <div className="flex justify-between items-center mb-4">
          <h2
            id="dokumen-saya-heading"
            className="text-xl font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            Dokumen Saya
          </h2>
          <Link
            href="/upload"
            className="px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            + Unggah Dokumen
          </Link>
        </div>

        {docsUsingMock && (
          <ApiStatusBanner context="Daftar dokumen menggunakan data contoh" />
        )}

        {docsLoading ? (
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white rounded-lg h-32 animate-pulse"
                style={{ border: "1px solid var(--color-border-card)" }}
              />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div
            className="text-center py-12 rounded-lg"
            style={{ border: "1px solid var(--color-border-card)", color: "var(--color-text-muted)" }}
          >
            <p className="text-lg">Belum ada dokumen. Unggah dokumen pertama Anda.</p>
            <Link
              href="/upload"
              className="text-sm mt-2 inline-block"
              style={{ color: "var(--color-primary)" }}
            >
              Unggah sekarang →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {documents.map((doc) => {
              const statusColor =
                doc.parsingStatus === "parsed"
                  ? { background: "#d1fae5", color: "#065f46" }
                  : doc.parsingStatus === "processing"
                    ? { background: "#fef9c3", color: "#92400e" }
                    : { background: "#fee2e2", color: "#991b1b" };

              const statusLabel =
                doc.parsingStatus === "parsed"
                  ? "Selesai"
                  : doc.parsingStatus === "processing"
                    ? "Diproses"
                    : "Gagal";

              const href =
                doc.isPublished && doc.moduleId
                  ? `/modules/${doc.moduleId}`
                  : `/upload/${doc.documentId}/review`;

              return (
                <article
                  key={doc.documentId}
                  role="article"
                  aria-label={`Dokumen: ${doc.title}`}
                  className="rounded-lg p-4"
                  style={{
                    border: "1px solid var(--color-border-card)",
                    background: "var(--color-surface)",
                  }}
                >
                  {/* Title */}
                  <h3 className="font-semibold text-base mb-2">
                    <Link
                      href={href}
                      style={{ color: "var(--color-primary)" }}
                    >
                      {doc.title}
                    </Link>
                  </h3>

                  {/* Badges row */}
                  <div className="flex flex-wrap gap-2 text-xs">
                    {/* File type */}
                    <span
                      className="px-2 py-0.5 rounded font-mono uppercase"
                      style={{ background: "var(--color-border-card)", color: "var(--color-text-secondary)" }}
                    >
                      {doc.fileType}
                    </span>

                    {/* Parsing status */}
                    <span
                      className="px-2 py-0.5 rounded font-medium"
                      style={statusColor}
                    >
                      {statusLabel}
                    </span>

                    {/* Published / Draft */}
                    <span
                      className="px-2 py-0.5 rounded font-medium"
                      style={
                        doc.isPublished
                          ? { background: "#d1fae5", color: "#065f46" }
                          : { background: "#e5e7eb", color: "#374151" }
                      }
                    >
                      {doc.isPublished ? "Terbit" : "Draft"}
                    </span>
                  </div>

                  {/* Math expressions count */}
                  <p
                    className="text-xs mt-2"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    {doc.mathExpressionsCount} ekspresi matematik
                  </p>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* Published Modules Section */}
      <section className="py-8" aria-labelledby="modul-terbit-heading">
        <div className="flex justify-between items-center mb-4">
          <h2
            id="modul-terbit-heading"
            className="text-xl font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            Modul yang Telah Diterbitkan
          </h2>
          <Link
            href="/upload"
            className="px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            + Unggah Baru
          </Link>
        </div>

        {modulesUsingMock && (
          <ApiStatusBanner context="Daftar modul menggunakan data contoh" />
        )}

        {modulesLoading ? (
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white rounded-lg h-48 animate-pulse"
                style={{ border: "1px solid var(--color-border-card)" }}
              />
            ))}
          </div>
        ) : modules.length === 0 ? (
          <div
            className="text-center py-12 rounded-lg"
            style={{ border: "1px solid var(--color-border-card)", color: "var(--color-text-muted)" }}
          >
            <p className="text-lg">Belum ada modul yang diterbitkan.</p>
            <Link
              href="/upload"
              className="text-sm mt-2 inline-block"
              style={{ color: "var(--color-primary)" }}
            >
              Unggah modul pertama Anda →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {modules.map((mod) => (
              <ModuleCard
                key={mod.id}
                category={mod.category}
                title={mod.title}
                grade={mod.grade}
                teacher={mod.teacher}
                features={mod.features}
                status={mod.status}
              />
            ))}
          </div>
        )}
      </section>

      {/* Keyboard Shortcuts Section */}
      <section className="py-8 mb-8">
        <KeyboardShortcuts />
      </section>
    </div>
  );
}
