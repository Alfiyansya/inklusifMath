"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { AuthBranding } from "@/components/auth/AuthBranding";
import { AuthCard } from "@/components/auth/AuthCard";
import type { User, UserRole } from "@/types";

type Step = "role" | "form" | "success";
type StudentLevel = "SD" | "SMP" | "SMA";

export default function RegisterPage() {
  const router = useRouter();
  const { user, register, isAuthenticated, isLoading } = useAuth();

  const [step, setStep] = useState<Step>("role");
  const [role, setRole] = useState<UserRole | null>(null);
  const [studentLevel, setStudentLevel] = useState<StudentLevel>("SD");

  /* Form fields */
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [registeredUser, setRegisteredUser] = useState<User | null>(null);

  /* Redirect if already authenticated (but not if just registered) */
  useEffect(() => {
    if (!isLoading && isAuthenticated && user && step !== "success") {
      const dest = user.role === "student" ? "/dashboard/student" : "/dashboard";
      router.replace(dest);
    }
  }, [isLoading, isAuthenticated, user, router, step]);

  /* Auto-redirect from success page after 3 seconds */
  useEffect(() => {
    if (step !== "success" || !registeredUser) return;
    const dest = registeredUser.role === "student" ? "/dashboard/student" : "/dashboard";
    const timer = setTimeout(() => {
      router.push(dest);
    }, 3000);
    return () => clearTimeout(timer);
  }, [step, registeredUser, router]);

  function selectRole(r: UserRole) {
    setRole(r);
    setStep("form");
    setError("");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!role) return;
    setError("");
    setSubmitting(true);

    try {
      const user = await register(email, password, fullName, role, role === "student" ? studentLevel : undefined);
      setRegisteredUser(user);
      setStep("success");
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

      {step === "role" && <RoleSelection onSelect={selectRole} />}
      {step === "form" && role && (
        <RegistrationForm
          role={role}
          studentLevel={studentLevel}
          setStudentLevel={setStudentLevel}
          fullName={fullName}
          setFullName={setFullName}
          email={email}
          setEmail={setEmail}
          password={password}
          setPassword={setPassword}
          showPassword={showPassword}
          setShowPassword={setShowPassword}
          error={error}
          submitting={submitting}
          onSubmit={handleSubmit}
          onBack={() => { setStep("role"); setError(""); }}
        />
      )}
      {step === "success" && registeredUser && (
        <SuccessScreen
          user={registeredUser}
          studentLevel={role === "student" ? studentLevel : undefined}
        />
      )}
    </main>
  );
}

/* ─────────────────────────────────────────────────────
   Step 1: Role Selection
   ───────────────────────────────────────────────────── */

function RoleSelection({
  onSelect,
}: {
  onSelect: (role: UserRole) => void;
}) {
  const roles = [
    {
      role: "teacher" as UserRole,
      icon: "👩‍🏫",
      title: "Guru",
      desc: "Unggah modul dan kelola narasi matematika",
    },
    {
      role: "student" as UserRole,
      icon: "🧑‍🎓",
      title: "Siswa",
      desc: "Akses modul dan gunakan tutor AI",
    },
  ];

  return (
    <AuthCard>
      <h1
        className="text-2xl font-extrabold text-center mb-2"
        style={{ color: "var(--color-text-primary)" }}
      >
        Daftar Akun
      </h1>
      <p
        className="text-sm text-center mb-8"
        style={{ color: "var(--color-text-secondary)" }}
      >
        Pilih peran Anda untuk melanjutkan
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {roles.map((r) => (
          <button
            key={r.role}
            onClick={() => onSelect(r.role)}
            className="flex flex-col items-center gap-3 p-6 rounded-2xl transition-all hover:scale-[1.02]"
            style={{
              border: "0.8px solid var(--color-border-card)",
              backgroundColor: "var(--color-bg-card)",
            }}
            aria-label={`Daftar sebagai ${r.title}`}
          >
            <span className="text-4xl" aria-hidden="true">
              {r.icon}
            </span>
            <span
              className="text-base font-bold"
              style={{ color: "var(--color-text-primary)" }}
            >
              {r.title}
            </span>
            <span
              className="text-xs text-center leading-relaxed"
              style={{ color: "var(--color-text-secondary)" }}
            >
              {r.desc}
            </span>
          </button>
        ))}
      </div>

      <p
        className="text-sm text-center mt-6"
        style={{ color: "var(--color-text-secondary)" }}
      >
        Sudah punya akun?{" "}
        <Link
          href="/login"
          className="font-semibold underline-offset-2 hover:underline"
          style={{ color: "var(--color-primary)" }}
        >
          Masuk di sini
        </Link>
      </p>
    </AuthCard>
  );
}

/* ─────────────────────────────────────────────────────
   Step 2: Registration Form
   ───────────────────────────────────────────────────── */

function RegistrationForm({
  role,
  studentLevel,
  setStudentLevel,
  fullName,
  setFullName,
  email,
  setEmail,
  password,
  setPassword,
  showPassword,
  setShowPassword,
  error,
  submitting,
  onSubmit,
  onBack,
}: {
  role: UserRole;
  studentLevel: StudentLevel;
  setStudentLevel: (v: StudentLevel) => void;
  fullName: string;
  setFullName: (v: string) => void;
  email: string;
  setEmail: (v: string) => void;
  password: string;
  setPassword: (v: string) => void;
  showPassword: boolean;
  setShowPassword: (v: boolean) => void;
  error: string;
  submitting: boolean;
  onSubmit: (e: FormEvent) => void;
  onBack: () => void;
}) {
  const isStudent = role === "student";
  const levels: StudentLevel[] = ["SD", "SMP", "SMA"];

  return (
    <AuthCard>
      {/* Back button */}
      <button
        type="button"
        onClick={onBack}
        className="flex items-center gap-1 text-sm font-medium mb-6 transition-colors"
        style={{ color: "var(--color-text-secondary)" }}
        aria-label="Kembali ke pilihan peran"
      >
        <svg
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
          <polyline points="15 18 9 12 15 6" />
        </svg>
        Kembali
      </button>

      <h1
        className="text-2xl font-extrabold text-center mb-2"
        style={{ color: "var(--color-text-primary)" }}
      >
        Daftar sebagai {isStudent ? "Siswa" : "Guru"}
      </h1>
      <p
        className="text-sm text-center mb-8"
        style={{ color: "var(--color-text-secondary)" }}
      >
        Lengkapi data berikut untuk membuat akun
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

      <form onSubmit={onSubmit} noValidate>
        {/* Full Name */}
        <div className="mb-4">
          <label
            htmlFor="reg-name"
            className="block text-sm font-medium mb-1.5"
            style={{ color: "var(--color-text-primary)" }}
          >
            Nama Lengkap
          </label>
          <input
            id="reg-name"
            type="text"
            autoComplete="name"
            required
            aria-required="true"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder={isStudent ? "Nama lengkap siswa" : "Nama lengkap guru"}
            className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-colors"
            style={{
              border: "0.8px solid var(--color-border-card)",
              color: "var(--color-text-primary)",
              backgroundColor: "var(--color-bg-card)",
            }}
          />
        </div>

        {/* Email */}
        <div className="mb-4">
          <label
            htmlFor="reg-email"
            className="block text-sm font-medium mb-1.5"
            style={{ color: "var(--color-text-primary)" }}
          >
            Email
          </label>
          <input
            id="reg-email"
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

        {/* Student Level (only for students) */}
        {isStudent && (
          <div className="mb-4">
            <label
              className="block text-sm font-medium mb-1.5"
              style={{ color: "var(--color-text-primary)" }}
            >
              Jenjang Pendidikan
            </label>
            <div className="grid grid-cols-3 gap-3" role="radiogroup" aria-label="Jenjang pendidikan">
              {levels.map((level) => (
                <button
                  key={level}
                  type="button"
                  role="radio"
                  aria-checked={studentLevel === level}
                  onClick={() => setStudentLevel(level)}
                  className="py-2.5 rounded-xl text-sm font-semibold transition-all"
                  style={{
                    border:
                      studentLevel === level
                        ? "2px solid var(--color-primary)"
                        : "0.8px solid var(--color-border-card)",
                    backgroundColor:
                      studentLevel === level ? "var(--color-tag-bg)" : "var(--color-bg-card)",
                    color:
                      studentLevel === level
                        ? "var(--color-primary)"
                        : "var(--color-text-secondary)",
                  }}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Password */}
        <div className="mb-6">
          <label
            htmlFor="reg-password"
            className="block text-sm font-medium mb-1.5"
            style={{ color: "var(--color-text-primary)" }}
          >
            Password
          </label>
          <div className="relative">
            <input
              id="reg-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              required
              aria-required="true"
              minLength={8}
              maxLength={128}
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
          {password.length > 0 && password.length < 8 && (
            <p className="text-xs mt-1.5" style={{ color: "#DC2626" }}>
              Password minimal 8 karakter
            </p>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting || !fullName || !email || password.length < 8}
          className="w-full py-3 rounded-xl text-sm font-bold text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            backgroundColor: submitting
              ? "var(--color-primary-hover)"
              : "var(--color-primary)",
          }}
        >
          {submitting ? "Mendaftarkan..." : "Daftar Sekarang"}
        </button>
      </form>

      <p
        className="text-sm text-center mt-6"
        style={{ color: "var(--color-text-secondary)" }}
      >
        Sudah punya akun?{" "}
        <Link
          href="/login"
          className="font-semibold underline-offset-2 hover:underline"
          style={{ color: "var(--color-primary)" }}
        >
          Masuk di sini
        </Link>
      </p>
    </AuthCard>
  );
}

/* ─────────────────────────────────────────────────────
   Step 3: Success Screen
   ───────────────────────────────────────────────────── */

function SuccessScreen({
  user,
  studentLevel,
}: {
  user: User;
  studentLevel?: StudentLevel;
}) {
  const isStudent = user.role === "student";
  const roleLabel = isStudent ? "Siswa" : "Guru";

  return (
    <AuthCard>
      <div className="flex flex-col items-center">
        {/* Success icon */}
        <div
          className="flex items-center justify-center rounded-full mb-5"
          style={{
            width: 80,
            height: 80,
            backgroundColor: "rgba(34, 211, 238, 0.12)",
          }}
        >
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M20 6L9 17L4 12"
              stroke="#F59E0B"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* Title */}
        <h1
          className="text-2xl font-extrabold text-center"
          style={{ color: "var(--color-text-primary)" }}
        >
          Pendaftaran Berhasil!
        </h1>

        {/* Welcome message */}
        <p
          className="text-sm text-center mt-2"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Selamat datang,{" "}
          <span className="font-bold" style={{ color: "var(--color-text-primary)" }}>
            {user.fullName}
          </span>
          .
        </p>

        {/* Role info */}
        <p
          className="text-sm text-center mt-1 flex items-center gap-1.5 justify-center"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Kamu terdaftar sebagai {roleLabel}
          {studentLevel && (
            <span
              className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-bold"
              style={{
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                color: "var(--color-primary)",
              }}
            >
              {studentLevel}
            </span>
          )}
        </p>

        {/* Redirect notice */}
        <p
          className="text-xs text-center mt-6 opacity-80"
          style={{ color: "var(--color-text-secondary)" }}
        >
          Mengalihkan ke dashboard…
        </p>
      </div>
    </AuthCard>
  );
}
