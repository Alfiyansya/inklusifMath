/**
 * Learning module API service functions.
 */

import { apiRequest } from "./client";

// ── Backend response types (snake_case matching Python schemas) ──

interface ModuleListItemApi {
  id: string;
  title: string;
  published_at: string;
}

interface ModuleListApiResponse {
  modules: ModuleListItemApi[];
}

interface MathExpressionApi {
  id: string;
  original_notation: string;
  latex: string | null;
  ai_narration: string | null;
  teacher_narration: string | null;
  status: string;
  position_order: number;
}

interface ModuleDetailApiResponse {
  id: string;
  title: string;
  html_content: string;
  math_expressions: MathExpressionApi[];
}

// ── Mapped frontend types (camelCase) ──

export interface ModuleListItem {
  id: string;
  title: string;
  publishedAt: string;
}

export interface ModuleDetail {
  id: string;
  title: string;
  htmlContent: string;
  mathExpressions: {
    id: string;
    originalNotation: string;
    latex: string | null;
    aiNarration: string | null;
    teacherNarration: string | null;
    status: string;
    positionOrder: number;
  }[];
}

// ── API Functions ──

export async function fetchModules(): Promise<ModuleListItem[]> {
  const res = await apiRequest<ModuleListApiResponse>("/modules");
  return res.modules.map((m) => ({
    id: m.id,
    title: m.title,
    publishedAt: m.published_at,
  }));
}

export async function fetchModuleDetail(
  moduleId: string,
): Promise<ModuleDetail> {
  const res = await apiRequest<ModuleDetailApiResponse>(
    `/modules/${moduleId}`,
  );
  return {
    id: res.id,
    title: res.title,
    htmlContent: res.html_content,
    mathExpressions: res.math_expressions.map((e) => ({
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
