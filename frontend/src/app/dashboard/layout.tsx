"use client";

import { useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Header } from "@/components/layout/Header";
import { TutorModal } from "@/components/tutor";
import { useTutor } from "@/hooks/useTutor";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading, isAuthenticated, logout } = useAuth();

  // Tutor button trigger ref — receives focus when modal closes
  const tutorTriggerRef = useRef<HTMLButtonElement>(null);

  // Tutor modal state — module context unknown at layout level, use "general"
  const tutor = useTutor({ moduleId: "general", contextElementId: "dashboard" });

  /* Auth guard: redirect to login if not authenticated */
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  /* Role-based routing guard */
  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      if (user.role === "student" && pathname === "/dashboard") {
        router.replace("/dashboard/student");
      }
      if (user.role === "teacher" && pathname === "/dashboard/student") {
        router.replace("/dashboard");
      }
    }
  }, [isLoading, isAuthenticated, user, pathname, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p style={{ color: "var(--color-text-muted)" }}>Memuat...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  const roleLabel = user.role === "teacher" ? "Guru" : user.role === "student" ? "Siswa" : "Admin";
  const initial = user.fullName ? user.fullName.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase();
  const displayName = user.fullName || user.email;

  return (
    <>
      <Header
        userName={displayName}
        userRole={roleLabel}
        userInitial={initial}
        studentLevel={user.role === "student" ? user.studentLevel : undefined}
        variant={user.role === "student" ? "student" : "teacher"}
        onOpenTutor={user.role === "student" ? tutor.openModal : undefined}
        tutorTriggerRef={user.role === "student" ? tutorTriggerRef : undefined}
        onLogout={async () => {
          await logout();
          router.push("/login");
        }}
      />
      <main id="main-content">{children}</main>

      {/* TutorModal — only mounted for student role */}
      {user.role === "student" && (
        <TutorModal
          isOpen={tutor.isOpen}
          status={tutor.status}
          messages={tutor.messages}
          transcript={tutor.transcript}
          liveAnnouncement={tutor.liveAnnouncement}
          isSpeechSupported={tutor.isSpeechSupported}
          isRecorderSupported={tutor.isRecorderSupported}
          onClose={tutor.closeModal}
          onTranscriptChange={tutor.setTranscript}
          onStartListening={tutor.startListening}
          onStopListening={tutor.stopListening}
          onSubmit={tutor.submitQuestion}
          onClear={tutor.clearConversation}
          triggerRef={tutorTriggerRef}
        />
      )}
    </>
  );
}
