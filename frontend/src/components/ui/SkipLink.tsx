/**
 * SkipLink — Allows keyboard/screen reader users to skip navigation.
 * WCAG 2.2 AA: Bypass Blocks (2.4.1)
 */

export function SkipLink({ targetId = 'main-content' }: { targetId?: string }) {
  return (
    <a
      href={`#${targetId}`}
      className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:bg-white focus:px-4 focus:py-2 focus:text-lg focus:font-semibold focus:text-blue-700 focus:shadow-lg focus:ring-2 focus:ring-blue-500 focus:rounded-md"
    >
      Langsung ke konten utama
    </a>
  );
}
