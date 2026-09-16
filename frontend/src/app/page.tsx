export default function Home() {
  return (
    <main
      id="main-content"
      className="flex min-h-screen flex-col items-center justify-center p-8"
    >
      <h1 className="text-4xl font-bold mb-4">InklusifMath</h1>
      <p className="text-xl text-gray-600 text-center max-w-2xl">
        Platform e-learning matematika aksesibel untuk siswa tunanetra dan low
        vision di Indonesia.
      </p>
      <p className="mt-4 text-gray-500">
        Tekan{" "}
        <kbd className="px-2 py-1 bg-gray-100 border rounded text-sm font-mono">
          Alt + T
        </kbd>{" "}
        untuk membuka tutor.
      </p>
    </main>
  );
}
