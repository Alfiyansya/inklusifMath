import React from "react";

export function KeyboardShortcuts() {
  const shortcuts = [
    { keys: ["Alt", "T"], description: "Buka / tutup Tutor Sokrates" },
    { keys: ["Spasi (tahan)"], description: "Rekam pertanyaan suara di modal tutor" },
    { keys: ["Escape"], description: "Tutup modal, kembalikan fokus" },
    { keys: ["Tab", "Shift+Tab"], description: "Navigasi antar elemen halaman" },
    { keys: ["Enter", "Spasi"], description: "Aktifkan tombol yang difokuskan" }
  ];

  return (
    <div className="bg-bg-page border border-border-card rounded-xl p-8" aria-labelledby="shortcuts-heading">
      <h2 id="shortcuts-heading" className="text-lg font-semibold text-text-primary mb-4">
        Pintasan Keyboard Global
      </h2>
      
      <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
        {shortcuts.map((shortcut, index) => (
          <div key={index} className="flex gap-3 items-start">
            <dt className="flex gap-1 flex-wrap flex-shrink-0">
              {shortcut.keys.map((key, i) => (
                <React.Fragment key={i}>
                  <kbd>{key}</kbd>
                  {i < shortcut.keys.length - 1 && shortcut.keys.length === 2 && shortcut.keys[1] !== "Shift+Tab" && (
                    <span className="text-text-secondary text-sm self-center" aria-hidden="true">+</span>
                  )}
                  {i < shortcut.keys.length - 1 && shortcut.keys[1] === "Shift+Tab" && (
                    <span className="text-text-secondary text-sm self-center mx-1" aria-hidden="true">/</span>
                  )}
                  {i < shortcut.keys.length - 1 && shortcut.keys[1] === "Spasi" && (
                    <span className="text-text-secondary text-sm self-center mx-1" aria-hidden="true">/</span>
                  )}
                </React.Fragment>
              ))}
            </dt>
            <dd className="text-sm text-text-secondary pt-0.5">
              {shortcut.description}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
