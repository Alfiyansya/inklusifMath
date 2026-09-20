"use client";

import { useAuth } from "@/context/AuthContext";
import { ApiStatusBanner } from "@/components/ui/ApiStatusBanner";
import { useModules } from "@/hooks/useModules";
import Link from "next/link";

export default function StudentDashboard() {
  const { user } = useAuth();
  const { modules, isLoading, isUsingMockData } = useModules();

  const firstName = user?.fullName?.split(" ")[0] ?? "Siswa";
  const levelLabel =
    user?.studentLevel === "SD"
      ? "Sekolah Dasar"
      : user?.studentLevel === "SMP"
        ? "Sekolah Menengah Pertama"
        : user?.studentLevel === "SMA"
          ? "Sekolah Menengah Atas"
          : "";

  /** Static topic categories — UI-only, not from API */
  const TOPICS = [
    { icon: "➕", label: "Penjumlahan & Pengurangan" },
    { icon: "✖️", label: "Perkalian & Pembagian" },
    { icon: "🍕", label: "Pecahan Dasar" },
    { icon: "🔢", label: "KPK & FPB" },
  ];

  return (
    <div className="max-w-[1152px] mx-auto px-4 sm:px-8 py-6 sm:py-10">
      {/* Welcome Card */}
      <section
        className="rounded-2xl p-8 relative overflow-hidden"
        style={{ border: "0.8px solid var(--color-border-card)" }}
      >
        <p className="text-sm font-bold" style={{ color: "var(--color-primary)" }}>
          {levelLabel}
        </p>
        <h1
          className="text-3xl font-extrabold mt-2"
          style={{ color: "var(--color-text-primary)" }}
        >
          Halo, {firstName}! 👋
        </h1>
        <p className="mt-2 max-w-md" style={{ color: "var(--color-text-secondary)" }}>
          Selamat datang di kelas matematikamu hari ini. Pilih modul di bawah untuk mulai belajar.
          Gunakan <strong>Alt + T</strong> kapan saja untuk bertanya ke Tutor Sokrates.
        </p>
        {/* Decorative circles */}
        <div
          className="absolute top-6 right-8 w-24 h-24 rounded-full opacity-60"
          style={{ backgroundColor: "var(--color-border-card)" }}
          aria-hidden="true"
        />
        <div
          className="absolute top-20 right-14 w-10 h-10 rounded-full opacity-40"
          style={{ backgroundColor: "#F59E0B" }}
          aria-hidden="true"
        />
      </section>

      {/* Progress Section */}
      <section className="mt-10">
        <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>
          Progres Belajarmu
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
          <ProgressCard
            current={3}
            total={Math.max(modules.length, 12)}
            label="Modul Selesai"
            color="var(--color-primary)"
          />
          <ProgressCard
            current={8}
            total={24}
            label="Bab Dibaca"
            color="var(--color-primary)"
          />
          <div
            className="rounded-xl p-5"
            style={{ border: "0.8px solid var(--color-border-card)" }}
          >
            <p className="text-3xl font-extrabold" style={{ color: "var(--color-primary)" }}>
              5<span className="text-lg">×</span>
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--color-text-secondary)" }}>
              Pertanyaan ke Tutor
            </p>
          </div>
        </div>
      </section>

      {/* Topics Section */}
      <section className="mt-10">
        <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>
          Topik yang Kamu Pelajari
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
          {TOPICS.map((topic) => (
            <div
              key={topic.label}
              className="flex flex-col items-center justify-center rounded-xl py-6 px-4 text-center"
              style={{ border: "0.8px solid var(--color-border-card)" }}
            >
              <span className="text-3xl mb-3" aria-hidden="true">{topic.icon}</span>
              <p className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
                {topic.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Modules Section */}
      <section className="mt-10">
        <h2 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>
          Modul Tersedia ({modules.length})
        </h2>

        {isUsingMockData && (
          <div className="mt-2">
            <ApiStatusBanner context="Daftar modul menggunakan data contoh" />
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="rounded-2xl h-48 animate-pulse bg-white"
                style={{ border: "0.8px solid var(--color-border-card)" }}
              />
            ))}
          </div>
        ) : modules.length === 0 ? (
          <div
            className="text-center py-12 rounded-2xl mt-4"
            style={{ border: "0.8px solid var(--color-border-card)", color: "var(--color-text-muted)" }}
          >
            <p className="text-lg">Belum ada modul tersedia.</p>
            <p className="text-sm mt-1">Guru sedang menyiapkan materi untukmu.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
            {modules.map((mod) => (
              <div
                key={mod.id}
                className="rounded-2xl overflow-hidden"
                style={{ border: "0.8px solid var(--color-border-card)" }}
              >
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <span
                      className="text-xs font-bold px-2.5 py-1 rounded-full"
                      style={{
                        backgroundColor: "rgba(100, 149, 237, 0.15)",
                        color: "var(--color-primary)",
                      }}
                    >
                      {mod.grade}
                    </span>
                    <span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
                      {mod.readingTime}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold" style={{ color: "var(--color-text-primary)" }}>
                    {mod.title}
                  </h3>
                  <p className="text-sm mt-1" style={{ color: "var(--color-text-secondary)" }}>
                    Oleh {mod.teacher}
                  </p>
                </div>
                <div className="px-6 pb-6">
                  <Link
                    href={`/modules/${mod.id}`}
                    className="block w-full py-3 rounded-xl font-bold text-sm text-white text-center hover:opacity-90 transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    style={{ backgroundColor: "var(--color-primary)" }}
                  >
                    Mulai Belajar
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Keyboard Guide */}
      <section className="mt-10 mb-10">
        <div
          className="rounded-2xl p-6"
          style={{ border: "0.8px solid var(--color-border-card)" }}
        >
          <h2 className="text-lg font-bold mb-4" style={{ color: "var(--color-text-primary)" }}>
            Panduan Keyboard
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ShortcutItem keys="Tab" desc="Pindah ke elemen berikutnya" />
            <ShortcutItem keys="Alt + T" desc="Buka Tutor Sokrates" />
            <ShortcutItem keys="Escape" desc="Tutup dialog" />
            <ShortcutItem keys="Enter / Spasi" desc="Aktifkan tombol" />
          </div>
        </div>
      </section>
    </div>
  );
}

/* ─── Sub-components ─── */

function ProgressCard({
  current,
  total,
  label,
  color,
}: {
  current: number;
  total: number;
  label: string;
  color: string;
}) {
  const pct = Math.round((current / total) * 100);

  return (
    <div
      className="rounded-xl p-5"
      style={{ border: "0.8px solid var(--color-border-card)" }}
    >
      <p className="text-3xl font-extrabold" style={{ color }}>
        {current}<span className="text-lg font-normal" style={{ color: "var(--color-text-secondary)" }}>/{total}</span>
      </p>
      <p className="text-sm mt-1" style={{ color: "var(--color-text-secondary)" }}>
        {label}
      </p>
      {/* Progress bar */}
      <div className="mt-3 h-1.5 w-full rounded-full bg-gray-100">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function ShortcutItem({ keys, desc }: { keys: string; desc: string }) {
  return (
    <div className="flex items-center gap-3">
      <kbd
        className="px-2.5 py-1 rounded text-xs font-bold border"
        style={{
          backgroundColor: "rgba(100, 149, 237, 0.1)",
          borderColor: "var(--color-border-card)",
          color: "var(--color-text-primary)",
        }}
      >
        {keys}
      </kbd>
      <span className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
        {desc}
      </span>
    </div>
  );
}
