"use client";

import { useState } from "react";
import Link from "next/link";
import { NarrationCard } from "@/components/teacher/NarrationCard";

export default function NarrationReviewPage() {
  const [narrations, setNarrations] = useState([
    { index: 1, notation: "a/b", latex: "\\frac{a}{b}", narration: "Pecahan. Pembilang: a. Penyebut: b.", confidence: 99, isApproved: false },
    { index: 2, notation: "1/(x+2)", latex: "\\frac{1}{x+2}", narration: "Pecahan. Pembilang: angka satu. Penyebut: x ditambah dua. Catatan: penyebut merupakan satu kesatuan ekspresi.", confidence: 97, isApproved: false },
    { index: 3, notation: "(3x-5)/2 = 8", latex: "\\frac{3x-5}{2} = 8", narration: "Persamaan linear: pecahan dengan pembilang tiga dikali x dikurangi lima, dan penyebut angka dua, sama dengan delapan.", confidence: 99, isApproved: false },
    { index: 4, notation: "2³ × 2⁴ = 2⁷", latex: "2^{3} \\times 2^{4} = 2^{7}", narration: "Persamaan perpangkatan: dua pangkat tiga, dikali dua pangkat empat, sama dengan dua pangkat tujuh.", confidence: 91, needsAttention: true, isApproved: false }
  ]);

  const handleNarrationChange = (index: number, newNarration: string) => {
    setNarrations(prev => prev.map(n => n.index === index ? { ...n, narration: newNarration, isApproved: false } : n));
  };

  const handleApprove = (index: number) => {
    setNarrations(prev => prev.map(n => n.index === index ? { ...n, isApproved: true } : n));
  };

  const remainingCount = narrations.filter(n => !n.isApproved).length;

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
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-text-primary mb-1">Tinjau Narasi Verbal</h2>
            <p className="text-text-secondary text-sm">Dokumen: Operasi_Bilangan.pdf &bull; 4 rumus ditemukan</p>
          </div>
          <button className="bg-primary text-white px-5 py-2.5 rounded-lg font-medium text-sm hover:bg-primary-hover transition-colors shadow-sm disabled:opacity-50" disabled={remainingCount === 0}>
            {remainingCount > 0 ? `Tinjau ${remainingCount} narasi tersisa` : 'Selesai Ditinjau'}
          </button>
        </div>

        <div className="flex gap-2 mb-8 border-b border-border-card pb-px">
          <button className="bg-primary text-white rounded-t-lg px-5 py-2 text-sm font-medium">
            Narasi Rumus
          </button>
          <button className="text-text-secondary hover:text-text-primary hover:bg-white/50 rounded-t-lg px-5 py-2 text-sm font-medium transition-colors">
            Pratinjau Dokumen
          </button>
        </div>

        <div className="max-w-4xl">
          {narrations.map(item => (
            <NarrationCard
              key={item.index}
              index={item.index}
              originalNotation={item.notation}
              latex={item.latex}
              aiNarration={item.narration}
              aiConfidence={item.confidence}
              needsAttention={item.needsAttention}
              isApproved={item.isApproved}
              teacherNarration={item.narration}
              onNarrationChange={(value) => handleNarrationChange(item.index, value)}
              onApprove={() => handleApprove(item.index)}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
