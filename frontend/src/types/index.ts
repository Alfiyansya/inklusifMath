// ============================================================
// InklusifMath Platform — Core Type Definitions
// Aligned with TDD Database Schema and API Specification
// ============================================================

// --- User & Auth ---
export type UserRole = 'teacher' | 'student' | 'admin';
export type StudentLevel = 'SD' | 'SMP' | 'SMA';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  fullName: string;
  studentLevel: StudentLevel | null;
  createdAt: string;
}

export interface AuthTokens {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  fullName: string;
  role: UserRole;
  studentLevel?: StudentLevel;
}

// --- Document ---
export type ParsingStatus = 'pending' | 'processing' | 'parsed' | 'failed';
export type OcrUsed = 'none' | 'gcv' | 'mathpix';

export interface Document {
  id: string;
  teacherId: string;
  title: string;
  fileType: 'docx' | 'pdf';
  parsingStatus: ParsingStatus;
  ocrUsed: OcrUsed;
  mathExpressionsCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentUploadResponse {
  documentId: string;
  title: string;
  status: ParsingStatus;
  message: string;
}

export interface DocumentProgress {
  step: 'extracting_text' | 'detecting_math' | 'generating_narration' | 'complete' | 'failed';
  progress: number;
  message: string;
}

// --- Math Expression ---
export type ExpressionStatus = 'pending' | 'ai_generated' | 'reviewed' | 'approved';

export interface MathExpression {
  id: string;
  originalNotation: string;
  latex: string | null;
  aiNarration: string | null;
  teacherNarration: string | null;
  status: ExpressionStatus;
  positionOrder: number;
}

export interface NarrationUpdateRequest {
  teacherNarration: string;
}

// --- Learning Module ---
export interface LearningModule {
  id: string;
  title: string;
  htmlContent: string;
  isPublished: boolean;
  publishedAt: string | null;
  mathExpressions: MathExpression[];
}

export interface LearningModuleListItem {
  id: string;
  title: string;
  publishedAt: string;
}

// --- Tutor ---
export interface TutorAskRequest {
  moduleId: string;
  contextElementId: string;
  transcriptText: string;
}

export interface TutorResponse {
  sessionId: string;
  answerText: string;
  followUpHint: string | null;
}

// --- Error ---
export interface ApiError {
  detail: string;
  errorCode?: string;
}
