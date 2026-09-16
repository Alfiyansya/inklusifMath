export function KeyboardShortcuts() {
  const shortcuts = [
    { keys: "Alt + T", description: "Buka / tutup Tutor Sokrates" },
    { keys: "Spasi\n(tahan)", description: "Rekam pertanyaan suara di modal tutor" },
    { keys: "Escape", description: "Tutup modal, kembalikan fokus" },
    { keys: "Tab /\nShift+Tab", description: "Navigasi antar elemen halaman" },
    { keys: "Enter /\nSpasi", description: "Aktifkan tombol yang difokuskan" },
  ];

  return (
    <div
      className="rounded-xl p-8"
      style={{
        backgroundColor: "var(--color-bg-page)",
        border: "1px solid var(--color-border-card)",
      }}
    >
      <h2
        className="text-lg font-semibold mb-4"
        style={{ color: "var(--color-text-primary)" }}
      >
        Pintasan Keyboard Global
      </h2>
      <dl className="grid grid-cols-3 gap-x-8 gap-y-4">
        {shortcuts.map((shortcut, index) => (
          <div key={index} className="flex gap-3 items-start">
            <dt>
              <kbd className="whitespace-pre-line text-center">
                {shortcut.keys}
              </kbd>
            </dt>
            <dd
              className="text-sm"
              style={{ color: "var(--color-text-secondary)" }}
            >
              {shortcut.description}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
