/**
 * STT API — POST /stt/transcribe
 *
 * Fallback speech-to-text for browsers without Web Speech API support.
 * Sends raw audio blob to backend faster-whisper endpoint.
 */

import { apiRequest } from "./client";

export interface SttTranscribeResponse {
  transcript: string;
  language: string;
  durationSeconds: number | null;
  modelUsed: string;
}

interface SttApiResponse {
  transcript: string;
  language: string;
  duration_seconds: number | null;
  model_used: string;
}

/**
 * Transcribe an audio Blob via the backend faster-whisper fallback.
 *
 * @param audioBlob - Audio recording (WAV, WebM, OGG, MP3), max 5 MB
 * @param filename - Optional filename hint for format detection
 */
export async function transcribeAudio(
  audioBlob: Blob,
  filename: string = "recording.webm"
): Promise<SttTranscribeResponse> {
  const formData = new FormData();
  formData.append("audio_file", audioBlob, filename);

  // apiRequest with FormData — don't set Content-Type (browser sets multipart boundary)
  const res = await apiRequest<SttApiResponse>("/stt/transcribe", {
    method: "POST",
    body: formData,
    // Content-Type is intentionally NOT set here — browser sets multipart/form-data
    headers: undefined,
  });

  return {
    transcript: res.transcript,
    language: res.language,
    durationSeconds: res.duration_seconds,
    modelUsed: res.model_used,
  };
}
