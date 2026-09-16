interface StatCardProps {
  value: string;
  label: string;
}

export function StatCard({ value, label }: StatCardProps) {
  return (
    <div
      className="bg-white rounded-lg py-5 text-center shadow-sm"
      style={{ border: "1px solid var(--color-border-card)" }}
    >
      <div className="text-3xl font-bold" style={{ color: "var(--color-primary)" }}>
        {value}
      </div>
      <div className="text-sm mt-1" style={{ color: "var(--color-text-secondary)" }}>
        {label}
      </div>
    </div>
  );
}
