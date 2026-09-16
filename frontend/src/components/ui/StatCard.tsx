import React from "react";

interface StatCardProps {
  value: string;
  label: string;
}

export function StatCard({ value, label }: StatCardProps) {
  return (
    <div className="bg-bg-card border border-border-card rounded-lg py-5 text-center shadow-sm">
      <div className="text-3xl font-bold text-primary">{value}</div>
      <div className="text-sm text-text-secondary mt-1">{label}</div>
    </div>
  );
}
