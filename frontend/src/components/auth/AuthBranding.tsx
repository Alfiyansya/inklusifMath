import Image from "next/image";

/**
 * AuthBranding — Logo + title header for login/register pages.
 * Matches Figma: 44px blue rounded square with logo, Poppins ExtraBold title.
 */
export function AuthBranding() {
  return (
    <div className="flex items-center gap-3 pb-8">
      <Image
        src="/logo.png"
        alt="Inklusif Math Logo"
        width={44}
        height={44}
        className="rounded-xl"
      />
      <div>
        <p
          className="text-lg font-extrabold leading-tight"
          style={{
            color: "var(--color-text-primary)",
            fontFamily: "'Poppins', sans-serif",
          }}
        >
          Inklusif Math
        </p>
        <p
          className="text-xs leading-tight"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Platform Matematika Inklusif
        </p>
      </div>
    </div>
  );
}
