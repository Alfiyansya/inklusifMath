"use client";

import Image from "next/image";
import { type RefObject } from "react";
import type { StudentLevel } from "@/types";

interface HeaderProps {
  userName: string;
  userRole: string;
  userInitial: string;
  variant?: "teacher" | "student";
  studentLevel?: StudentLevel | null;
  onLogout?: () => void;
  /** Called when student clicks "Tanya Tutor" button */
  onOpenTutor?: () => void;
  /** Ref attached to the Tanya Tutor button — receives focus when modal closes */
  tutorTriggerRef?: RefObject<HTMLButtonElement | null>;
}

export function Header({
  userName,
  userRole,
  userInitial,
  variant = "teacher",
  studentLevel,
  onLogout,
  onOpenTutor,
  tutorTriggerRef,
}: HeaderProps) {
  return (
    <header
      className="bg-white"
      style={{ borderBottom: "0.8px solid var(--color-border-card)" }}
    >
      <div className="max-w-[1152px] mx-auto px-8 py-4 flex items-center justify-between">
        {/* Logo + Brand */}
        <div className="flex items-center gap-3">
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
              style={{ color: "var(--color-text-primary)", fontFamily: "'Poppins', sans-serif" }}
            >
              InklusifMath
            </p>
            {variant === "student" ? (
              <p
                className="text-xs leading-tight font-medium"
                style={{ color: "var(--color-primary)" }}
              >
                Siswa {studentLevel ? `· ${studentLevel}` : ""}
              </p>
            ) : (
              <p
                className="text-xs leading-tight"
                style={{ color: "var(--color-text-secondary)" }}
              >
                Platform Matematika Inklusif
              </p>
            )}
          </div>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-3">
          {/* Student: Tanya Tutor button */}
          {variant === "student" && (
            <button
              ref={tutorTriggerRef}
              onClick={onOpenTutor}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold text-white focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary transition-opacity hover:opacity-90"
              style={{ backgroundColor: "var(--color-primary)" }}
              aria-label="Buka Tutor Sokrates (Alt+T)"
            >
              <span aria-hidden="true">✏️</span>
              Tanya Tutor
            </button>
          )}

          {/* User info */}
          <div className="text-right">
            <p
              className="text-sm font-semibold leading-tight"
              style={{ color: "var(--color-text-primary)" }}
            >
              {userName}
            </p>
            <p
              className="text-xs leading-tight"
              style={{ color: "var(--color-text-secondary)" }}
            >
              {userRole}
            </p>
          </div>

          {/* Avatar */}
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold"
            style={{
              backgroundColor: "var(--color-avatar-bg)",
              color: "var(--color-text-primary)",
            }}
          >
            {userInitial}
          </div>

          {/* Logout */}
          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-semibold transition-colors"
            style={{
              border: "0.8px solid var(--color-border-card)",
              color: "var(--color-text-secondary)",
            }}
            aria-label="Keluar dari akun"
          >
            <svg
              width="15"
              height="15"
              viewBox="0 0 15 15"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M5.625 13.125H3.125C2.79348 13.125 2.47554 12.9933 2.24112 12.7589C2.0067 12.5245 1.875 12.2065 1.875 11.875V3.125C1.875 2.79348 2.0067 2.47554 2.24112 2.24112C2.47554 2.0067 2.79348 1.875 3.125 1.875H5.625M10 10.625L13.125 7.5M13.125 7.5L10 4.375M13.125 7.5H5.625"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Keluar
          </button>
        </div>
      </div>
    </header>
  );
}
