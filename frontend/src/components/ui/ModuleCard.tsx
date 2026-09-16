"use client";

interface ModuleCardProps {
  category: string;
  title: string;
  grade: string;
  teacher: string;
  features: string[];
  status: "published" | "draft" | "review";
  onView?: () => void;
}

export function ModuleCard({
  category,
  title,
  grade,
  teacher,
  features,
  status,
  onView,
}: ModuleCardProps) {
  return (
    <article
      className="bg-white rounded-lg overflow-hidden shadow-sm flex flex-col h-full"
      style={{ border: "1px solid var(--color-border-card)" }}
      aria-label={`Modul: ${title}`}
    >
      <div className="p-6 flex-grow">
        <span
          className="uppercase text-xs font-semibold block mb-1"
          style={{ color: "var(--color-primary)" }}
        >
          {category}
        </span>
        <h3
          className="text-lg font-semibold leading-tight mb-2"
          style={{ color: "var(--color-text-primary)" }}
        >
          {title}
        </h3>
        <p className="text-sm mb-4" style={{ color: "var(--color-text-secondary)" }}>
          {grade} &middot; {teacher}
        </p>

        {features && features.length > 0 && (
          <div className="flex flex-wrap gap-2" aria-label="Fitur aksesibilitas modul">
            {features.map((feature, index) => (
              <span
                key={index}
                className="text-xs font-medium px-2 py-1 rounded-full"
                style={{
                  backgroundColor: "var(--color-tag-bg)",
                  color: "var(--color-tag-text)",
                }}
              >
                {feature}
              </span>
            ))}
          </div>
        )}
      </div>

      <div
        className="px-6 py-4 flex items-center justify-between mt-auto"
        style={{ borderTop: "1px solid var(--color-border-card)" }}
      >
        <button
          onClick={onView}
          className="flex-grow rounded-md py-2 text-sm text-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1"
          style={{
            backgroundColor: "var(--color-bg-page)",
            border: "1px solid var(--color-border-card)",
            color: "var(--color-text-primary)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-primary)";
            e.currentTarget.style.color = "#fff";
            e.currentTarget.style.borderColor = "var(--color-primary)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-bg-page)";
            e.currentTarget.style.color = "var(--color-text-primary)";
            e.currentTarget.style.borderColor = "var(--color-border-card)";
          }}
          aria-label={`Lihat modul ${title}`}
        >
          Lihat
        </button>

        {status === "published" && (
          <span
            className="ml-4 text-sm font-medium flex items-center gap-1 flex-shrink-0"
            style={{ color: "var(--color-success)" }}
            aria-label="Status: Terbit"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Terbit
          </span>
        )}
      </div>
    </article>
  );
}
