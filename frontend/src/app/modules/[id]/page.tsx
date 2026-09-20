"use client";

/**
 * /modules/[id] — Halaman baca modul siswa.
 *
 * Ini adalah halaman utama untuk siswa tunanetra/low-vision.
 * Implementasi TDD Section 7 (Math Rendering), ADR-003 (MathJax dual-layer),
 * FR-09 (navigasi heading semantik), FR-10 (dual-layer representation),
 * FR-15 (aria-live), WCAG 2.2 AA.
 *
 * Arsitektur dual-layer:
 *   - html_content dari backend dirender sebagai semantic HTML (h1-h6, p, table)
 *   - MathExpression ditempatkan inline di antara konten teks
 *   - Setiap formula: MathDisplay (MathJax visual) + aria-label narasi guru/AI
 *
 * Aksesibilitas:
 *   - <main id="main-content"> sebagai landmark utama
 *   - Skip link ke konten
 *   - Heading semantik dari raw_structure dokumen (h1 = judul modul, h2 = bab, dll.)
 *   - formula bisa difokuskan via Tab (tabIndex=0 di MathDisplay)
 *   - aria-label narasi Indonesia menjadi sumber bacaan screen reader
 *   - "Rumus ke-N" label untuk navigasi
 *   - Keyboard shortcut: Alt+T = Tutor, Arrow = scroll, J/K = prev/next formula
 *
 * Navigasi rumus dengan keyboard (J/K):
 *   - Implementasi sederhana: kumpulkan semua elemen [data-math-index], J/K focus prev/next
 */

import { useParams } from "next/navigation";
import Link from "next/link";
import { useEffect, useRef, useCallback } from "react";
import { MathDisplay } from "@/components/math";
import { ApiStatusBanner } from "@/components/ui/ApiStatusBanner";
import { useModuleDetail } from "@/hooks/useModuleDetail";
import { TutorModal } from "@/components/tutor";
import { useTutor } from "@/hooks/useTutor";

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function ModuleReaderPage() {
  const params = useParams();
  const moduleId = params.id as string;
  const { module, isLoading, isUsingMockData } = useModuleDetail(moduleId);
  const contentRef = useRef<HTMLDivElement>(null);
  const tutorButtonRef = useRef<HTMLButtonElement>(null);

  // Tutor AI modal hook (handles Alt+T shortcut internally)
  const tutor = useTutor({ moduleId });

  // J/K keyboard navigation between math formulas
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Only trigger if not inside a text input/textarea
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return;

      if (e.key !== "j" && e.key !== "k") return;

      const formulas = Array.from(
        document.querySelectorAll<HTMLElement>("[data-math-index]")
      );
      if (formulas.length === 0) return;

      const focused = document.activeElement as HTMLElement | null;
      const currentIdx = focused?.dataset?.mathIndex
        ? parseInt(focused.dataset.mathIndex, 10)
        : -1;

      const nextIdx =
        e.key === "j"
          ? Math.min(currentIdx + 1, formulas.length - 1)
          : Math.max(currentIdx - 1, 0);

      formulas[nextIdx]?.focus();
      e.preventDefault();
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  // ── Loading skeleton ────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-page">
        <ModuleHeader title="Memuat modul…" moduleId={moduleId} />
        <main className="container max-w-[860px] mx-auto px-8 py-10" aria-busy="true">
          <div className="space-y-4">
            <div className="h-8 bg-white rounded-xl animate-pulse" style={{ border: "1px solid var(--color-border-card)" }} />
            <div className="h-4 bg-white rounded animate-pulse w-3/4" style={{ border: "1px solid var(--color-border-card)" }} />
            <div className="h-4 bg-white rounded animate-pulse w-5/6" style={{ border: "1px solid var(--color-border-card)" }} />
            <div className="h-20 bg-white rounded-xl animate-pulse mt-8" style={{ border: "1px solid var(--color-border-card)" }} />
            <div className="h-4 bg-white rounded animate-pulse" style={{ border: "1px solid var(--color-border-card)" }} />
            <div className="h-4 bg-white rounded animate-pulse w-4/5" style={{ border: "1px solid var(--color-border-card)" }} />
          </div>
        </main>
      </div>
    );
  }

  if (!module) {
    return (
      <div className="min-h-screen bg-bg-page flex items-center justify-center">
        <div className="text-center">
          <p className="text-4xl mb-4">🔍</p>
          <h1 className="text-xl font-bold text-text-primary">Modul tidak ditemukan</h1>
          <p className="text-text-secondary text-sm mt-1 mb-6">
            Modul ini mungkin belum dipublikasikan atau tidak tersedia.
          </p>
          <Link
            href="/modules"
            className="bg-primary text-white px-6 py-3 rounded-lg text-sm font-medium hover:opacity-90"
          >
            Kembali ke Daftar Modul
          </Link>
        </div>
      </div>
    );
  }

  const expressions = module.mathExpressions ?? [];
  const approvedCount = expressions.filter((e) => e.status === "approved").length;

  return (
    <div className="min-h-screen bg-bg-page">
      {/* Skip link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-white px-4 py-2 rounded-lg z-50 text-sm font-medium"
      >
        Langsung ke konten modul
      </a>

      <ModuleHeader title={module.title} moduleId={moduleId} />

      {/* Reader layout: sidebar + content */}
      <div className="container max-w-[1152px] mx-auto px-4 sm:px-8 py-6 sm:py-8 flex gap-8">

        {/* ── Sidebar: daftar rumus ── */}
        <aside
          className="w-64 shrink-0 hidden lg:block"
          aria-label="Daftar rumus dalam modul"
        >
          <div
            className="bg-white rounded-xl p-4 sticky top-24"
            style={{ border: "0.8px solid var(--color-border-card)" }}
          >
            <h2 className="text-xs font-bold uppercase tracking-wider text-text-muted mb-3">
              Rumus dalam Modul
            </h2>
            {expressions.length === 0 ? (
              <p className="text-xs text-text-muted italic">Tidak ada rumus</p>
            ) : (
              <nav aria-label="Navigasi rumus">
                <ul className="space-y-1">
                  {expressions.map((expr, idx) => (
                    <li key={expr.id}>
                      <button
                        onClick={() => {
                          document
                            .querySelector<HTMLElement>(`[data-math-index="${idx}"]`)
                            ?.focus();
                        }}
                        className="w-full text-left text-xs py-1.5 px-2 rounded hover:bg-bg-page text-text-secondary hover:text-primary transition-colors truncate"
                        title={expr.originalNotation}
                      >
                        #{idx + 1} {expr.originalNotation}
                      </button>
                    </li>
                  ))}
                </ul>
              </nav>
            )}

            {/* Keyboard shortcut hint */}
            <div
              className="mt-4 pt-4 text-xs text-text-muted space-y-1"
              style={{ borderTop: "1px solid var(--color-border-card)" }}
            >
              <p className="font-semibold uppercase tracking-wider mb-2">Pintasan Keyboard</p>
              <p><kbd className="bg-bg-page border border-border-card rounded px-1 font-mono">J</kbd> → rumus berikutnya</p>
              <p><kbd className="bg-bg-page border border-border-card rounded px-1 font-mono">K</kbd> → rumus sebelumnya</p>
              <p><kbd className="bg-bg-page border border-border-card rounded px-1 font-mono">Alt+T</kbd> → Tutor Sokrates</p>
            </div>
          </div>
        </aside>

        {/* ── Main content ── */}
        <main id="main-content" className="flex-1 min-w-0">
          {isUsingMockData && (
            <div className="mb-6">
              <ApiStatusBanner context="Konten modul menggunakan data contoh" />
            </div>
          )}

          {/* Module meta bar */}
          <div
            className="bg-white rounded-xl px-6 py-4 mb-6 flex items-center justify-between flex-wrap gap-2"
            style={{ border: "0.8px solid var(--color-border-card)" }}
          >
            <div>
              <h1 className="text-2xl font-extrabold text-text-primary">
                {module.title}
              </h1>
              <p className="text-sm text-text-secondary mt-0.5">
                {expressions.length} ekspresi matematika &bull;{" "}
                {approvedCount} narasi terverifikasi guru
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="text-xs px-2.5 py-1 rounded-full font-medium"
                style={{
                  backgroundColor: "rgba(34, 197, 94, 0.1)",
                  color: "var(--color-success)",
                  border: "0.8px solid rgba(34,197,94,0.2)",
                }}
              >
                ✓ Dipublikasikan
              </span>
            </div>
          </div>

          {/* Semantic HTML content + inline MathDisplay */}
          <article
            ref={contentRef}
            className="bg-white rounded-xl px-8 py-8"
            style={{ border: "0.8px solid var(--color-border-card)" }}
          >
            {/* Render html_content */}
            <ModuleContent
              htmlContent={module.htmlContent}
              expressions={expressions}
            />
          </article>

          {/* Formula gallery (below content) */}
          {expressions.length > 0 && (
            <section
              className="mt-8 bg-white rounded-xl px-8 py-6"
              style={{ border: "0.8px solid var(--color-border-card)" }}
              aria-labelledby="formula-gallery-heading"
            >
              <h2
                id="formula-gallery-heading"
                className="text-lg font-bold text-text-primary mb-6"
              >
                Galeri Rumus ({expressions.length})
              </h2>

              <div className="space-y-4">
                {expressions.map((expr, idx) => (
                  <FormulaCard
                    key={expr.id}
                    index={idx}
                    expression={expr}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Navigation footer */}
          <nav
            className="flex justify-between items-center mt-8 pb-8"
            aria-label="Navigasi modul"
          >
            <Link
              href="/modules"
              className="text-sm text-text-secondary hover:text-primary transition-colors font-medium flex items-center gap-1"
            >
              &larr; Kembali ke Daftar Modul
            </Link>
            <Link
              href="/dashboard/student"
              className="text-sm text-text-secondary hover:text-primary transition-colors font-medium"
            >
              Beranda Siswa →
            </Link>
          </nav>
        </main>
      </div>

      {/* ── Floating Tutor button ── */}
      <button
        ref={tutorButtonRef}
        onClick={tutor.openModal}
        aria-label="Buka dialog tutor AI (Alt+T)"
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-white transition-transform hover:scale-105 focus-visible:ring-4 focus-visible:ring-offset-2 focus-visible:ring-primary z-30"
        style={{ backgroundColor: "var(--color-primary)" }}
      >
        <span className="text-2xl" aria-hidden="true">🦉</span>
      </button>

      {/* ── Tutor Sokrates modal ── */}
      <TutorModal
        isOpen={tutor.isOpen}
        onClose={tutor.closeModal}
        status={tutor.status}
        messages={tutor.messages}
        transcript={tutor.transcript}
        liveAnnouncement={tutor.liveAnnouncement}
        isSpeechSupported={tutor.isSpeechSupported}
        isRecorderSupported={tutor.isRecorderSupported}
        onTranscriptChange={tutor.setTranscript}
        onStartListening={tutor.startListening}
        onStopListening={tutor.stopListening}
        onSubmit={tutor.submitQuestion}
        onClear={tutor.clearConversation}
        triggerRef={tutorButtonRef}
      />
    </div>
  );
}

// ── Module content renderer ────────────────────────────────────────────────────

/**
 * ModuleContent renders the backend's html_content as semantic HTML.
 *
 * The html_content is XSS-safe (produced by _build_html_from_structure in
 * document_service.py). We use dangerouslySetInnerHTML for rich content —
 * the content never comes from user-submitted HTML, only from backend-generated
 * semantic structure.
 *
 * Math expressions are shown inline as MathDisplay components in the Formula
 * Gallery section below, not inside the HTML string (which would require
 * hydration of arbitrary DOM nodes). This is the pragmatic approach.
 */
function ModuleContent({
  htmlContent,
  expressions,
}: {
  htmlContent: string;
  expressions: Array<{
    id: string;
    originalNotation: string;
    latex: string | null;
    aiNarration: string | null;
    teacherNarration: string | null;
    status: string;
    positionOrder: number;
  }>;
}) {
  // Build a substitution map: original_notation → latex + narration
  // so we can detect in-text mentions and show a small inline formula indicator
  const exprMap = new Map(
    expressions.map((e) => [e.originalNotation.toLowerCase(), e])
  );

  void exprMap; // Map built for future inline substitution pass

  return (
    <div
      className="prose prose-sm max-w-none
        prose-h2:text-xl prose-h2:font-bold prose-h2:text-text-primary prose-h2:mt-8 prose-h2:mb-3
        prose-h3:text-lg prose-h3:font-semibold prose-h3:text-text-primary prose-h3:mt-6 prose-h3:mb-2
        prose-p:text-text-secondary prose-p:leading-relaxed
        prose-table:border prose-table:border-border-card
        prose-td:p-3 prose-th:p-3 prose-th:bg-bg-page
        focus-within:ring-0"
      /* Backend-generated safe HTML from raw_structure blocks */
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  );
}

// ── Formula Card ──────────────────────────────────────────────────────────────

/**
 * FormulaCard — aksesibel card untuk satu ekspresi matematika.
 *
 * ADR-003 dual-layer:
 *   - MathDisplay (visual MathJax + aria-label narasi)
 *   - data-math-index untuk J/K keyboard navigation
 */
function FormulaCard({
  index,
  expression,
}: {
  index: number;
  expression: {
    id: string;
    originalNotation: string;
    latex: string | null;
    aiNarration: string | null;
    teacherNarration: string | null;
    status: string;
    positionOrder: number;
  };
}) {
  const narration = expression.teacherNarration ?? expression.aiNarration;
  const isVerified = expression.status === "approved";

  return (
    <div
      className={`rounded-xl overflow-hidden`}
      style={{ border: `1px solid ${isVerified ? "rgba(34,197,94,0.3)" : "var(--color-border-card)"}` }}
    >
      {/* Formula header */}
      <div
        className="px-4 py-2 flex items-center justify-between"
        style={{ backgroundColor: "var(--color-bg-page)", borderBottom: "1px solid var(--color-border-card)" }}
      >
        <span className="text-xs font-mono text-text-muted">
          Rumus #{index + 1}
        </span>
        <span className="font-medium text-text-secondary text-sm truncate mx-3 flex-1">
          {expression.originalNotation}
        </span>
        {isVerified ? (
          <span className="text-xs text-success font-medium shrink-0">✓ Terverifikasi</span>
        ) : (
          <span className="text-xs text-warning font-medium shrink-0">AI</span>
        )}
      </div>

      {/* Formula body: MathDisplay + narration */}
      <div className="px-6 py-5 flex flex-col items-center gap-4 sm:flex-row sm:items-start">
        {/* Visual layer — MathJax */}
        <div
          className="flex items-center justify-center min-w-[120px] min-h-[48px] p-4 rounded-lg"
          style={{ backgroundColor: "var(--color-bg-page)", border: "1px solid var(--color-border-card)" }}
        >
          {expression.latex ? (
            <MathDisplay
              latex={expression.latex}
              teacherNarration={expression.teacherNarration}
              aiNarration={expression.aiNarration}
              display={false}
              className="text-lg"
            />
          ) : (
            <code className="font-mono text-sm text-text-secondary">
              {expression.originalNotation}
            </code>
          )}
        </div>

        {/* Verbal layer — narasi Indonesia */}
        <div className="flex-1">
          <p className="text-xs uppercase tracking-wider text-text-muted font-semibold mb-1">
            Narasi Verbal
          </p>
          {narration ? (
            <p
              className="text-base text-text-primary font-medium leading-relaxed"
              /* This element's ID could be referenced as aria-describedby
                 by the MathDisplay above for even tighter coupling */
              data-math-index={index}
              tabIndex={0}
              role="note"
              aria-label={`Rumus ${index + 1}: ${narration}`}
            >
              &ldquo;{narration}&rdquo;
            </p>
          ) : (
            <p className="text-sm text-text-muted italic">
              Narasi belum tersedia untuk rumus ini.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Module Header ─────────────────────────────────────────────────────────────

function ModuleHeader({
  title,
  moduleId,
}: {
  title: string;
  moduleId: string;
}) {
  void moduleId; // reserved for breadcrumb or share links
  return (
    <header className="bg-white border-b border-border-card px-4 sm:px-8 py-4 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <Link
          href="/modules"
          className="text-text-secondary hover:text-primary transition-colors text-sm font-medium"
        >
          &larr; Daftar Modul
        </Link>
        <div className="h-4 w-px bg-border-card" aria-hidden="true" />
        <span className="font-semibold text-text-primary truncate max-w-xs">{title}</span>
      </div>
      <span className="text-xs text-text-muted font-medium uppercase tracking-wider shrink-0">
        InklusifMath
      </span>
    </header>
  );
}
