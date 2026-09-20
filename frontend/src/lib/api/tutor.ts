/**
 * Tutor API — POST /tutor/ask
 */

import { apiRequest } from "./client";

export interface TutorAskPayload {
  moduleId: string;
  contextElementId: string;
  transcriptText: string;
}

export interface TutorAskResponse {
  sessionId: string;
  answerText: string;
  followUpHint: string | null;
}

interface TutorAskApiResponse {
  session_id: string;
  answer_text: string;
  follow_up_hint: string | null;
}

export async function askTutor(
  payload: TutorAskPayload
): Promise<TutorAskResponse> {
  const res = await apiRequest<TutorAskApiResponse>("/tutor/ask", {
    method: "POST",
    body: JSON.stringify({
      module_id: payload.moduleId,
      context_element_id: payload.contextElementId,
      transcript_text: payload.transcriptText,
    }),
  });

  return {
    sessionId: res.session_id,
    answerText: res.answer_text,
    followUpHint: res.follow_up_hint,
  };
}
