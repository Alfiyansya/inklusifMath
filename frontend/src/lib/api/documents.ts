/**
 * Document API service functions.
 * Handles upload, narrations, and approval endpoints.
 */

import { apiRequest } from "./client";

// ── Backend response types (snake_case matching Python schemas) ──

interface DocumentUploadApiResponse {
  document_id: string;
  title: string;
  status: string;
  message: string;
}

interface MathExpressionApiResponse {
  id: string;
  original_notation: string;
  latex: string | null;
  ai_narration: string | null;
  teacher_narration: string | null;
  status: string;
  position_order: number;
}

interface NarrationListApiResponse {
  document_id: string;
  title: string;
  expressions: MathExpressionApiResponse[];
}

interface NarrationUpdateApiResponse {
  id: string;
  status: string;
  teacher_narration: string;
}

interface ApproveApiResponse {
  module_id: string;
  document_id: string;
  is_published: boolean;
  published_at: string;
}

// ── Mapped frontend types (camelCase) ──

export interface DocumentUploadResult {
  documentId: string;
  title: string;
  status: string;
  message: string;
}

export interface NarrationItem {
  id: string;
  originalNotation: string;
  latex: string | null;
  aiNarration: string | null;
  teacherNarration: string | null;
  status: string;
  positionOrder: number;
}

export interface NarrationListResult {
  documentId: string;
  title: string;
  expressions: NarrationItem[];
}

export interface ApproveResult {
  moduleId: string;
  documentId: string;
  isPublished: boolean;
  publishedAt: string;
}

// ── API Functions ──

export async function uploadDocument(
  file: File,
  title: string,
): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);

  const res = await apiRequest<DocumentUploadApiResponse>(
    "/documents/upload",
    { method: "POST", body: formData },
  );

  return {
    documentId: res.document_id,
    title: res.title,
    status: res.status,
    message: res.message,
  };
}

export async function fetchDocumentNarrations(
  documentId: string,
): Promise<NarrationListResult> {
  const res = await apiRequest<NarrationListApiResponse>(
    `/documents/${documentId}/narrations`,
  );

  return {
    documentId: res.document_id,
    title: res.title,
    expressions: res.expressions.map((e) => ({
      id: e.id,
      originalNotation: e.original_notation,
      latex: e.latex,
      aiNarration: e.ai_narration,
      teacherNarration: e.teacher_narration,
      status: e.status,
      positionOrder: e.position_order,
    })),
  };
}

export async function updateNarration(
  narrationId: string,
  teacherNarration: string,
): Promise<{ id: string; status: string; teacherNarration: string }> {
  const res = await apiRequest<NarrationUpdateApiResponse>(
    `/documents/narrations/${narrationId}`,
    {
      method: "PATCH",
      body: JSON.stringify({ teacher_narration: teacherNarration }),
    },
  );

  return {
    id: res.id,
    status: res.status,
    teacherNarration: res.teacher_narration,
  };
}

export async function approveDocument(
  documentId: string,
): Promise<ApproveResult> {
  const res = await apiRequest<ApproveApiResponse>(
    `/documents/${documentId}/approve`,
    { method: "POST" },
  );

  return {
    moduleId: res.module_id,
    documentId: res.document_id,
    isPublished: res.is_published,
    publishedAt: res.published_at,
  };
}

// ── Document List & Detail types ──────────────────────────────────────────────

interface DocumentListItemApiResponse {
  document_id: string;
  title: string;
  file_type: string;
  parsing_status: string;
  ocr_used: string;
  math_expressions_count: number;
  is_published: boolean;
  module_id: string | null;
  created_at: string;
  updated_at: string;
}

interface DocumentListApiResponse {
  documents: DocumentListItemApiResponse[];
  total: number;
  limit: number;
  offset: number;
}

interface DocumentDetailApiResponse {
  document_id: string;
  title: string;
  file_type: string;
  parsing_status: string;
  ocr_used: string;
  error_code: string | null;
  math_expressions_count: number;
  narrations_pending: number;
  narrations_ai_generated: number;
  narrations_reviewed: number;
  narrations_approved: number;
  is_published: boolean;
  module_id: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListItem {
  documentId: string;
  title: string;
  fileType: string;
  parsingStatus: string;
  ocrUsed: string;
  mathExpressionsCount: number;
  isPublished: boolean;
  moduleId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentListResult {
  documents: DocumentListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentDetailResult {
  documentId: string;
  title: string;
  fileType: string;
  parsingStatus: string;
  ocrUsed: string;
  errorCode: string | null;
  mathExpressionsCount: number;
  narrationsPending: number;
  narrationsAiGenerated: number;
  narrationsReviewed: number;
  narrationsApproved: number;
  isPublished: boolean;
  moduleId: string | null;
  publishedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export async function fetchDocumentList(
  limit = 50,
  offset = 0,
): Promise<DocumentListResult> {
  const res = await apiRequest<DocumentListApiResponse>(
    `/documents?limit=${limit}&offset=${offset}`,
  );
  return {
    documents: res.documents.map((d) => ({
      documentId: d.document_id,
      title: d.title,
      fileType: d.file_type,
      parsingStatus: d.parsing_status,
      ocrUsed: d.ocr_used,
      mathExpressionsCount: d.math_expressions_count,
      isPublished: d.is_published,
      moduleId: d.module_id,
      createdAt: d.created_at,
      updatedAt: d.updated_at,
    })),
    total: res.total,
    limit: res.limit,
    offset: res.offset,
  };
}

export async function fetchDocumentDetail(
  documentId: string,
): Promise<DocumentDetailResult> {
  const res = await apiRequest<DocumentDetailApiResponse>(
    `/documents/${documentId}`,
  );
  return {
    documentId: res.document_id,
    title: res.title,
    fileType: res.file_type,
    parsingStatus: res.parsing_status,
    ocrUsed: res.ocr_used,
    errorCode: res.error_code,
    mathExpressionsCount: res.math_expressions_count,
    narrationsPending: res.narrations_pending,
    narrationsAiGenerated: res.narrations_ai_generated,
    narrationsReviewed: res.narrations_reviewed,
    narrationsApproved: res.narrations_approved,
    isPublished: res.is_published,
    moduleId: res.module_id,
    publishedAt: res.published_at,
    createdAt: res.created_at,
    updatedAt: res.updated_at,
  };
}
