"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  updateProfile,
} from "firebase/auth";
import { auth } from "@/lib/firebase";
import { createUserProfile, getUserProfile } from "@/lib/firestore";
import type { User, UserRole, StudentLevel } from "@/types";

/* ─── Context value ─── */
interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (
    email: string,
    password: string,
    fullName: string,
    role: UserRole,
    studentLevel?: StudentLevel,
  ) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/* ─── Helper: Firebase error → Indonesian message ─── */
function getFirebaseErrorMessage(code: string): string {
  switch (code) {
    case "auth/email-already-in-use":
      return "Email sudah terdaftar. Silakan gunakan email lain.";
    case "auth/invalid-email":
      return "Format email tidak valid.";
    case "auth/weak-password":
      return "Password terlalu lemah. Minimal 6 karakter.";
    case "auth/user-not-found":
    case "auth/wrong-password":
    case "auth/invalid-credential":
      return "Email atau password salah.";
    case "auth/too-many-requests":
      return "Terlalu banyak percobaan. Silakan coba lagi nanti.";
    case "auth/network-request-failed":
      return "Gagal terhubung ke server. Periksa koneksi internet Anda.";
    default:
      return "Terjadi kesalahan. Silakan coba lagi.";
  }
}

/* ─── Provider ─── */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /* Listen to Firebase auth state + fetch Firestore profile */
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      // Always clear previous user first to prevent stale state on account switch
      setUser(null);
      setIsLoading(true);

      if (firebaseUser) {
        try {
          const profile = await getUserProfile(firebaseUser.uid);
          if (profile) {
            setUser({
              id: firebaseUser.uid,
              email: firebaseUser.email ?? profile.email,
              role: profile.role,
              fullName: profile.fullName,
              studentLevel: profile.studentLevel,
              createdAt: "",
            });
          } else {
            // Firebase user exists but no Firestore profile yet
            // (happens briefly during register flow)
            setUser({
              id: firebaseUser.uid,
              email: firebaseUser.email ?? "",
              role: "student",
              fullName: firebaseUser.displayName ?? "",
              studentLevel: null,
              createdAt: "",
            });
          }
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  /* ─── Login ─── */
  const login = useCallback(async (email: string, password: string): Promise<User> => {
    try {
      const credential = await signInWithEmailAndPassword(auth, email, password);
      const profile = await getUserProfile(credential.user.uid);

      const loggedInUser: User = {
        id: credential.user.uid,
        email: credential.user.email ?? email,
        role: profile?.role ?? "student",
        fullName: profile?.fullName ?? credential.user.displayName ?? "",
        studentLevel: profile?.studentLevel ?? null,
        createdAt: "",
      };
      setUser(loggedInUser);
      return loggedInUser;
    } catch (error: unknown) {
      const firebaseError = error as { code?: string };
      throw new Error(getFirebaseErrorMessage(firebaseError.code ?? ""));
    }
  }, []);

  /* ─── Register ─── */
  const register = useCallback(
    async (
      email: string,
      password: string,
      fullName: string,
      role: UserRole,
      studentLevel?: StudentLevel,
    ): Promise<User> => {
      try {
        // Step 1: Create Firebase user
        const credential = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(credential.user, { displayName: fullName });

        // Step 2: Create Firestore profile
        await createUserProfile(credential.user.uid, {
          role,
          fullName,
          email,
          studentLevel: role === "student" ? studentLevel : undefined,
        });

        const newUser: User = {
          id: credential.user.uid,
          email,
          role,
          fullName,
          studentLevel: role === "student" ? (studentLevel ?? null) : null,
          createdAt: "",
        };
        setUser(newUser);
        return newUser;
      } catch (error: unknown) {
        const firebaseError = error as { code?: string; message?: string };
        if (firebaseError.code) {
          throw new Error(getFirebaseErrorMessage(firebaseError.code));
        }
        throw error;
      }
    },
    [],
  );

  /* ─── Logout ─── */
  const logout = useCallback(async () => {
    await signOut(auth);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/* ─── Hook ─── */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
