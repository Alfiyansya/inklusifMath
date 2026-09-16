export function FeatureList() {
  const features = [
    {
      icon: "🔇",
      title: "Zero Audio Collision",
      description:
        "Tidak ada suara web yang mengganggu screen reader Anda.",
    },
    {
      icon: "∑",
      title: "Rumus Dual-Layer",
      description:
        "Setiap formula memiliki narasi verbal Bahasa Indonesia yang lengkap.",
    },
    {
      icon: "🎤",
      title: "Tutor Push-to-Talk",
      description:
        "Tanya Tutor Sokrates kapan saja dengan Alt + T dan rekam suara.",
    },
    {
      icon: "⌨",
      title: "Keyboard-Only",
      description:
        "Seluruh platform dapat dioperasikan penuh tanpa mouse.",
    },
  ];

  return (
    <div
      className="rounded-xl p-6"
      style={{
        backgroundColor: "var(--color-bg-page)",
        border: "1px solid var(--color-border-card)",
      }}
      aria-labelledby="features-heading"
    >
      <h2 id="features-heading" className="sr-only">
        Fitur Aksesibilitas
      </h2>
      <div className="flex flex-col gap-6">
        {features.map((feature, index) => (
          <div key={index} className="flex gap-4">
            <div
              className="w-9 h-9 flex-shrink-0 bg-white rounded-lg flex items-center justify-center text-lg shadow-sm"
              style={{ border: "1px solid var(--color-border-card)" }}
              aria-hidden="true"
            >
              {feature.icon}
            </div>
            <div>
              <h3
                className="font-medium text-sm mb-1"
                style={{ color: "var(--color-text-primary)" }}
              >
                {feature.title}
              </h3>
              <p
                className="text-sm leading-relaxed"
                style={{ color: "var(--color-text-secondary)" }}
              >
                {feature.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
