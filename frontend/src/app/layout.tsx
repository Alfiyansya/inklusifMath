import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { SkipLink } from "@/components/ui/SkipLink";
import { AuthProvider } from "@/context/AuthContext";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "InklusifMath — Platform Matematika Aksesibel",
  description:
    "Platform e-learning matematika aksesibel untuk siswa tunanetra dan low vision di Indonesia.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="id" className={`${inter.variable} h-full antialiased`}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Poppins:wght@800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col" style={{ fontFamily: "'Inter', sans-serif" }}>
        <SkipLink />
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
