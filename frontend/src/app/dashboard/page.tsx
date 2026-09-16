import Link from "next/link";
import { FeatureList } from "@/components/ui/FeatureList";
import { StatCard } from "@/components/ui/StatCard";
import { ModuleCard } from "@/components/ui/ModuleCard";
import { KeyboardShortcuts } from "@/components/ui/KeyboardShortcuts";

export default function TeacherDashboard() {
  const publishedModules = [
    { category: "MATEMATIKA SD", title: "Operasi Bilangan Bulat", grade: "Kelas 4 SD", teacher: "Bu Sari Dewi", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const },
    { category: "MATEMATIKA SD", title: "Operasi Bilangan Pecahan", grade: "Kelas 5 SD", teacher: "Bu Sari Dewi", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const },
    { category: "MATEMATIKA SD", title: "KPK dan FPB", grade: "Kelas 5 SD", teacher: "Pak Rudi Hartono", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const },
    { category: "MATEMATIKA SD", title: "Perkalian dan Pembagian", grade: "Kelas 4 SD", teacher: "Bu Sari Dewi", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const },
    { category: "ALJABAR SMP", title: "Pengantar Persamaan Linear", grade: "Kelas 7 SMP", teacher: "Pak Budi Santoso", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const },
    { category: "MATEMATIKA SMP", title: "Rasio dan Proporsi", grade: "Kelas 7 SMP", teacher: "Bu Ani Rahayu", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const },
    { category: "MATEMATIKA SMP", title: "Bilangan Bulat Negatif", grade: "Kelas 7 SMP", teacher: "Pak Budi Santoso", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const },
    { category: "MATEMATIKA SMP", title: "Persentase dan Desimal", grade: "Kelas 8 SMP", teacher: "Bu Ani Rahayu", features: ["Keyboard navigasi", "Rumus naratif", "Tutor AI"], status: "published" as const }
  ];

  return (
    <div className="container max-w-[1152px] mx-auto px-8">
        {/* Hero Section */}
        <section className="py-10">
          <div className="grid grid-cols-2 gap-16 items-start">
            <div>
              <h1 className="text-5xl font-bold leading-tight">Belajar Matematika<br/><span className="text-primary">Tanpa Hambatan</span></h1>
              <p className="text-text-secondary text-lg leading-relaxed mt-4">
                Platform pembelajaran matematika yang dirancang secara inklusif. Unggah modul Anda, dan sistem AI kami akan membuatnya dapat diakses oleh semua siswa, termasuk mereka yang memiliki keterbatasan visual.
              </p>
              <Link href="/upload" className="bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-hover mt-8 inline-block transition-colors">
                Unggah Modul &rarr;
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
            <StatCard value="24" label="Modul Tersedia" />
            <StatCard value="8" label="Guru Aktif" />
            <StatCard value="137" label="Siswa Terdaftar" />
            <StatCard value="100%" label="Kepatuhan WCAG" />
          </div>
        </section>

        {/* Published Modules Section */}
        <section className="py-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Modul yang Telah Diterbitkan</h2>
            <Link href="/upload" className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors hover:bg-primary-hover">
              + Unggah Baru
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {publishedModules.map((module, i) => (
              <ModuleCard key={i} {...module} />
            ))}
          </div>
        </section>

        {/* Keyboard Shortcuts Section */}
        <section className="py-8 mb-8">
          <KeyboardShortcuts />
        </section>
    </div>
  );
}
