"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useState, useCallback, useEffect } from "react";
import { NarrationCard } from "@/components/teacher/NarrationCard";
import { ApiStatusBanner } from "@/components/ui/ApiStatusBanner";
import { useNarrations } from "@/hooks/useNarrations";
import { ParsingProgress } from "@/components/ui/ParsingProgress";
import { LiveRegion } from "@/components/ui/LiveRegion";
import { fetchDocumentDetail } from "@/lib/api/documents";

// ── Publish Success Screen ────────────────────────────────────────────────────

function PublishSuccessScreen({
  moduleId,
  documentTitle,
}: {
  moduleId: string;
  documentTitle: string;
}) {
  return (
    <div className="min-h-screen bg-bg-page flex items-center justify-center">
      <div
        className="bg-white rounded-2xl p-10 max-w-lg w-full mx-4 text-center shadow-sm"
        style={{ border: "2px solid var(--color-success)" }}
        role="alert"
        aria-live="assertive"
      >
        {/* Success icon */}
        <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-5">
          <svg
            className="w-8 h-8 text-success"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Modul Berhasil Dipublikasikan!
        </h1>
        <p className="text-text-secondary text-sm mb-1">
          <strong>{documentTitle}</strong> telah disetujui dan dipublikasikan
          sebagai modul aksesibel untuk siswa.
        </p>
        <p className="text-text-muted text-xs mb-8">
          Siswa tunanetra dapat mengakses modul ini dengan screen reader mereka.
        </p>

        <div className="flex flex-col gap-3">
          <Link
            href={`/modules/${moduleId}`}
            className="bg-primary text-white px-6 py-3 rounded-lg font-medium text-sm hover:bg-primary-hover transition-colors"
          >
            Lihat Modul Siswa →
          </Link>
          <Link
            href="/dashboard"
            className="text-text-secondary text-sm hover:text-text-primary transition-colors"
          >
            Kembali ke Beranda
          </Link>
        </div>
      </div>
    </div>
  );
}

// ── Progress Bar ──────────────────────────────────────────────────────────────

function ApprovalProgress({
  approved,
  total,
}: {
  approved: number;
  total: number;
}) {
  const pct = total > 0 ? Math.round((approved / total) * 100) : 0;
  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs font-medium text-text-secondary">
          Progress Persetujuan
        </span>
        <span className="text-xs font-semibold text-text-primary">
          {approved}/{total} disetujui ({pct}%)
        </span>
      </div>
      <div
        className="h-2 bg-bg-page rounded-full overflow-hidden"
        style={{ border: "1px solid var(--color-border-card)" }}
        role="progressbar"
        aria-valuenow={approved}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={`${approved} dari ${total} narasi disetujui`}
      >
        <div
          className="h-full bg-primary rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Main Review Page ──────────────────────────────────────────────────────────

export default function NarrationReviewPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;
  const [publishedModuleId, setPublishedModuleId] = useState<string | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [activeTab, setActiveTab] = useState<"narasi" | "pratinjau">("narasi");

  // Track whether the document has finished parsing
  const [parsingStatus, setParsingStatus] = useState<string | null>(null);

  // Fetch document parsing_status on mount to decide whether to show progress
  useEffect(() => {
    if (!documentId) return;
    fetchDocumentDetail(documentId)
      .then((doc) => setParsingStatus(doc.parsingStatus))
      .catch(() => setParsingStatus("done")); // On error, assume done so we don't block
  }, [documentId]);

  // Re-fetch document status after SSE completes (called by ParsingProgress)
  const refetchParsingStatus = useCallback(
    async (completedStatus: string) => {
      setParsingStatus(completedStatus);
    },
    []
  );

  const {
    narrations,
    documentTitle,
    isLoading,
    isUsingMockData,
    remainingCount,
    editNarration,
    saveNarration,
    approveNarration,
    approveAll,
  } = useNarrations(documentId);

  const approvedCount = narrations.filter((n) => n.isApproved).length;
  const allApproved = remainingCount === 0 && narrations.length > 0;

  // Show parsing progress if status is not yet done/error (and we know the status)
  const showParsingProgress =
    parsingStatus !== null && parsingStatus !== "done" && parsingStatus !== "error";

  const [publishError, setPublishError] = useState<string | null>(null);

  // Publish: save all unsaved, then approve
  const handlePublish = useCallback(async () => {
    setIsPublishing(true);
    setPublishError(null);
    try {
      const result = await approveAll();
      // approveAll returns ApproveResult | undefined (mock returns undefined)
      if (result && "moduleId" in result) {
        setPublishedModuleId((result as { moduleId: string }).moduleId);
      } else {
        // Mock data or no module_id — redirect to modules list
        router.push("/dashboard/student");
      }
    } catch (err: unknown) {
      setPublishError(
        err instanceof Error
          ? err.message
          : "Gagal mempublikasikan modul. Silakan coba lagi."
      );
    } finally {
      setIsPublishing(false);
    }
  }, [approveAll, router]);

  // ── Loading skeleton ──
  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-page">
        <PageHeader documentTitle="Memuat…" />
        <main className="container max-w-[1152px] mx-auto px-8 py-8">
          <div className="max-w-4xl space-y-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="bg-white rounded-xl h-48 animate-pulse"
                style={{ border: "2px solid var(--color-border-card)" }}
              />
            ))}
          </div>
        </main>
      </div>
    );
  }

  // ── Publish success screen ──
  if (publishedModuleId) {
    return (
      <PublishSuccessScreen
        moduleId={publishedModuleId}
        documentTitle={documentTitle}
      />
    );
  }

  return (
    <div className="min-h-screen bg-bg-page">
      <PageHeader documentTitle={documentTitle} />

      <main className="container max-w-[1152px] mx-auto px-4 sm:px-8 py-6 sm:py-8">
        {/* Title + publish button */}
        <div className="flex flex-col sm:flex-row justify-between sm:items-start mb-6 gap-4">
          <div>
            <h2 className="text-2xl font-bold text-text-primary mb-1">
              Tinjau Narasi Verbal
            </h2>
            <p className="text-text-secondary text-sm">
              Dokumen: <strong>{documentTitle}</strong> &bull;{" "}
              {narrations.length} rumus ditemukan
            </p>
          </div>

          <button
            onClick={handlePublish}
            disabled={isPublishing || (!allApproved && !isUsingMockData)}
            className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-colors shadow-sm flex items-center gap-2 shrink-0 ${
              allApproved || isUsingMockData
                ? "bg-primary text-white hover:bg-primary-hover"
                : "bg-bg-page text-text-muted border border-border-card cursor-not-allowed"
            } disabled:opacity-60`}
            title={
              !allApproved && !isUsingMockData
                ? `Setujui semua ${remainingCount} narasi terlebih dahulu`
                : undefined
            }
          >
            {isPublishing ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Mempublikasikan…
              </>
            ) : allApproved ? (
              "Publikasikan Modul ✓"
            ) : (
              `${remainingCount} narasi belum disetujui`
            )}
          </button>
        </div>

        {/* Screen reader announcement for publish errors */}
        <LiveRegion message={publishError ?? ""} politeness="assertive" />

        {/* Error alert box */}
        {publishError && (
          <div
            role="alert"
            aria-live="assertive"
            aria-atomic="true"
            className="rounded-lg px-4 py-3 mb-6 text-sm"
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              color: "#DC2626",
              border: "1px solid rgba(239, 68, 68, 0.2)",
            }}
          >
            {publishError}
          </div>
        )}

        {/* Mock data warning */}
        {isUsingMockData && (
          <ApiStatusBanner context="Narasi menggunakan data contoh — backend tidak tersedia" />
        )}

        {/* SSE Parsing Progress Indicator */}
        {showParsingProgress && (
          <ParsingProgress
            documentId={documentId}
            onComplete={refetchParsingStatus}
          />
        )}

        {/* Progress bar */}
        {narrations.length > 0 && (
          <ApprovalProgress
            approved={approvedCount}
            total={narrations.length}
          />
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-8 border-b border-border-card pb-px">
          <button
            onClick={() => setActiveTab("narasi")}
            className={`rounded-t-lg px-5 py-2 text-sm font-medium transition-colors ${
              activeTab === "narasi"
                ? "bg-primary text-white"
                : "text-text-secondary hover:text-text-primary hover:bg-white/50"
            }`}
            aria-selected={activeTab === "narasi"}
            role="tab"
          >
            Narasi Rumus ({narrations.length})
          </button>
          <button
            onClick={() => setActiveTab("pratinjau")}
            className={`rounded-t-lg px-5 py-2 text-sm font-medium transition-colors ${
              activeTab === "pratinjau"
                ? "bg-primary text-white"
                : "text-text-secondary hover:text-text-primary hover:bg-white/50"
            }`}
            aria-selected={activeTab === "pratinjau"}
            role="tab"
          >
            Pratinjau Dokumen
          </button>
        </div>

        {/* Tab content */}
        {activeTab === "narasi" ? (
          <div className="max-w-4xl" role="tabpanel">
            {narrations.length === 0 ? (
              <div className="bg-white rounded-xl p-10 text-center" style={{ border: "2px solid var(--color-border-card)" }}>
                <p className="text-text-muted">Tidak ada ekspresi matematika ditemukan dalam dokumen ini.</p>
              </div>
            ) : (
              narrations.map((item) => (
                <NarrationCard
                  key={item.id}
                  index={item.positionOrder}
                  originalNotation={item.originalNotation}
                  latex={item.latex ?? ""}
                  aiNarration={item.aiNarration ?? ""}
                  aiConfidence={item.aiConfidence}
                  needsAttention={item.needsAttention}
                  isApproved={item.isApproved}
                  isSaving={item.isSaving}
                  teacherNarration={item.localNarration}
                  onNarrationChange={(value) => editNarration(item.id, value)}
                  onSave={() => saveNarration(item.id)}
                  onApprove={() => approveNarration(item.id)}
                />
              ))
            )}
          </div>
        ) : (
          // Pratinjau tab — raw HTML content from backend
          <div className="max-w-4xl" role="tabpanel">
            <div
              className="bg-white rounded-xl p-8 prose prose-sm max-w-none"
              style={{ border: "2px solid var(--color-border-card)" }}
            >
              <p className="text-text-muted text-sm italic">
                Pratinjau dokumen akan tampil setelah modul dipublikasikan.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// ── Shared Header ─────────────────────────────────────────────────────────────

function PageHeader({ documentTitle }: { documentTitle: string }) {
  return (
    <header className="bg-white border-b border-border-card px-8 py-4 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <Link
          href="/dashboard"
          className="text-text-secondary hover:text-primary transition-colors text-sm font-medium"
        >
          &larr; Beranda
        </Link>
        <div className="h-4 w-px bg-border-card" />
        <span className="font-semibold text-text-primary">
          Portal Guru &mdash; {documentTitle}
        </span>
      </div>
      <span className="text-xs text-text-muted font-medium uppercase tracking-wider">
        InklusifMath
      </span>
    </header>
  );
}
