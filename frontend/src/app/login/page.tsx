"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { AuthBranding } from "@/components/auth/AuthBranding";
import { AuthCard } from "@/components/auth/AuthCard";

export default function LoginPage() {
  const router = useRouter();
  const { user, login, isAuthenticated, isLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  /* Redirect if already authenticated */
  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      const dest = user.role === "student" ? "/dashboard/student" : "/dashboard";
      router.replace(dest);
    }
  }, [isLoading, isAuthenticated, user, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const loggedInUser = await login(email, password);
      const dest = loggedInUser.role === "student" ? "/dashboard/student" : "/dashboard";
      router.push(dest);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Terjadi kesalahan. Silakan coba lagi.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p style={{ color: "var(--color-text-muted)" }}>Memuat...</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      <AuthBranding />

      <AuthCard>
        <h1
          className="text-2xl font-extrabold text-center mb-2"
          style={{ color: "var(--color-text-primary)" }}
        >
          Masuk
        </h1>
        <p
          className="text-sm text-center mb-8"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Masukkan email dan password Anda
        </p>

        {/* Error message */}
        {error && (
          <div
            role="alert"
            aria-live="polite"
            className="rounded-lg px-4 py-3 mb-6 text-sm"
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              color: "#DC2626",
              border: "1px solid rgba(239, 68, 68, 0.2)",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          {/* Email */}
          <div className="mb-4">
            <label
              htmlFor="login-email"
              className="block text-sm font-medium mb-1.5"
              style={{ color: "var(--color-text-primary)" }}
            >
              Email
            </label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              required
              aria-required="true"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nama@email.com"
              className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-colors"
              style={{
                border: "0.8px solid var(--color-border-card)",
                color: "var(--color-text-primary)",
                backgroundColor: "var(--color-bg-card)",
              }}
            />
          </div>

          {/* Password */}
          <div className="mb-6">
            <label
              htmlFor="login-password"
              className="block text-sm font-medium mb-1.5"
              style={{ color: "var(--color-text-primary)" }}
            >
              Password
            </label>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                aria-required="true"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimal 8 karakter"
                className="w-full px-4 py-3 pr-12 rounded-xl text-sm outline-none transition-colors"
                style={{
                  border: "0.8px solid var(--color-border-card)",
                  color: "var(--color-text-primary)",
                  backgroundColor: "var(--color-bg-card)",
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                aria-label={showPassword ? "Sembunyikan password" : "Tampilkan password"}
                style={{ color: "var(--color-text-muted)" }}
              >
                {showPassword ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting || !email || !password}
            className="w-full py-3 rounded-xl text-sm font-bold text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              backgroundColor: submitting ? "var(--color-primary-hover)" : "var(--color-primary)",
            }}
          >
            {submitting ? "Memproses..." : "Masuk"}
          </button>
        </form>

        {/* Register link */}
        <p
          className="text-sm text-center mt-6"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Belum punya akun?{" "}
          <Link
            href="/register"
            className="font-semibold underline-offset-2 hover:underline"
            style={{ color: "var(--color-primary)" }}
          >
            Daftar di sini
          </Link>
        </p>
      </AuthCard>
    </main>
  );
}
