/**
 * Firestore user profile operations.
 * Stores user roles, names, and student levels in the `users` collection.
 */

import { doc, getDoc, setDoc, serverTimestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";
import type { UserRole, StudentLevel } from "@/types";

export interface UserProfile {
  role: UserRole;
  fullName: string;
  email: string;
  studentLevel: StudentLevel | null;
  createdAt: unknown; // Firestore Timestamp
}

/**
 * Create a user profile document in Firestore after Firebase Auth signup.
 */
export async function createUserProfile(
  uid: string,
  data: {
    role: UserRole;
    fullName: string;
    email: string;
    studentLevel?: StudentLevel;
  },
): Promise<void> {
  const userRef = doc(db, "users", uid);
  await setDoc(userRef, {
    role: data.role,
    fullName: data.fullName,
    email: data.email,
    studentLevel: data.role === "student" ? (data.studentLevel ?? null) : null,
    createdAt: serverTimestamp(),
  });
}

/**
 * Get a user profile from Firestore by UID.
 * Returns null if no profile exists.
 */
export async function getUserProfile(uid: string): Promise<UserProfile | null> {
  const userRef = doc(db, "users", uid);
  const snap = await getDoc(userRef);
  if (!snap.exists()) return null;
  return snap.data() as UserProfile;
}
