"use client";

import React from "react";

interface NarrationCardProps {
  index: number;
  originalNotation: string;
  latex: string;
  aiNarration: string;
  aiConfidence: number; // 0-100
  teacherNarration?: string;
  isApproved?: boolean;
  needsAttention?: boolean; // true if confidence < 95
  onNarrationChange?: (value: string) => void;
  onApprove?: () => void;
}

export const NarrationCard: React.FC<NarrationCardProps> = ({
  index,
  originalNotation,
  latex,
  aiNarration,
  aiConfidence,
  teacherNarration,
  isApproved,
  needsAttention = false,
  onNarrationChange,
  onApprove,
}) => {
  const isLowConfidence = aiConfidence < 95;
  const currentNarration = teacherNarration ?? aiNarration;

  return (
    <div className={`bg-white border-2 rounded-xl overflow-hidden mb-6 ${needsAttention ? 'border-warning' : 'border-border-card'}`}>
      <div className="bg-bg-page px-5 py-3 rounded-t-xl flex justify-between items-center border-b border-border-card">
        <div className="flex items-center gap-3">
          <span className="bg-white border border-border-card rounded px-2 py-0.5 text-xs font-mono text-text-secondary">#{index}</span>
          <span className="font-medium text-text-primary">{originalNotation}</span>
        </div>
        {needsAttention && (
          <span className="bg-warning/10 text-warning text-xs font-medium px-2 py-1 rounded">
            ⚠ Perlu Perhatian
          </span>
        )}
      </div>
      
      <div className="grid grid-cols-2 divide-x divide-border-card">
        {/* Left Column */}
        <div className="p-5">
          <p className="uppercase text-xs tracking-wider text-text-muted font-semibold mb-3">TAMPILAN VISUAL (LATEX)</p>
          <div className="bg-bg-page rounded p-3 font-mono text-sm mb-4 text-text-primary overflow-x-auto">
            {latex}
          </div>
          <div className="border border-primary/30 bg-primary/5 rounded p-2 inline-block mb-4">
            <span className="text-primary font-mono text-lg">{latex}</span>
          </div>
          <p className="text-xs text-text-muted mt-2">
            Keyakinan AI: <span className={isLowConfidence ? 'font-bold' : ''}>{aiConfidence}%</span>
          </p>
        </div>

        {/* Right Column */}
        <div className="p-5 flex flex-col">
          <p className="uppercase text-xs tracking-wider text-text-muted font-semibold mb-3">NARASI VERBAL INDONESIA (DAPAT DIEDIT)</p>
          <textarea
            className="w-full min-h-[100px] border border-border-card rounded-lg p-4 text-sm resize-y focus:border-primary focus:ring-1 focus:ring-primary outline-none mb-2"
            value={currentNarration}
            onChange={(e) => onNarrationChange?.(e.target.value)}
          />
          <p className="text-xs text-text-muted mb-4">Teks ini akan dimasukkan ke atribut aria-label pada rumus.</p>
          <div className="mt-auto">
            <button 
              onClick={onApprove}
              className={`w-full border rounded-lg py-2.5 text-sm font-medium transition-colors ${
                isApproved 
                  ? 'bg-success text-white border-success' 
                  : 'bg-white border-border-card text-text-primary hover:bg-primary hover:text-white hover:border-primary'
              }`}
            >
              {isApproved ? 'Telah Disetujui ✓' : 'Setujui Narasi'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
