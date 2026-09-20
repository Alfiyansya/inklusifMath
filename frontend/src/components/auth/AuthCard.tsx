import type { ReactNode } from "react";

/**
 * AuthCard — White card container for auth forms.
 * Matches Figma: white bg, #C8DCFA border, 16px radius, max-width 512px.
 */
export function AuthCard({ children }: { children: ReactNode }) {
  return (
    <div
      className="w-full max-w-[512px] rounded-2xl overflow-hidden"
      style={{
        backgroundColor: "var(--color-bg-card)",
        border: "0.8px solid var(--color-border-card)",
      }}
    >
      <div className="px-5 sm:px-10 py-8 sm:py-12">{children}</div>
    </div>
  );
}
