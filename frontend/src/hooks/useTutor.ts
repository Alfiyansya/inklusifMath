"use client";

/**
 * useTutor — Manages Tutor Sokrates modal state, Web Speech API STT,
 * and POST /tutor/ask communication.
 *
 * Responsibilities:
 *   - Open/close modal
 *   - Web Speech API recognition (primary STT, browser-native, free)
 *   - Fallback: typed text input when speech unavailable
 *   - POST to /tutor/ask, parse response
 *   - Wire earcons: start-record, stop-record, response-ready, error
 *   - Expose aria-live message for screen reader announcement
 *   - Alt+T global shortcut (via useGlobalShortcut)
 */

import { useState, useCallback, useRef } from "react";
import { askTutor } from "@/lib/api/tutor";
import { transcribeAudio } from "@/lib/api/stt";
import {
  earconRecordStart,
  earconRecordStop,
  earconResponseReady,
  earconError,
} from "@/lib/audio/earcon";
import { useGlobalShortcut } from "./useGlobalShortcut";

// ── Web Speech API type declarations ─────────────────────────────────────────
// The Web Speech API is a browser API not yet in TypeScript's lib.dom.d.ts.
// We declare only what we use.

interface SpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  readonly transcript: string;
  readonly confidence: number;
}

interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number;
  readonly results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string;
  readonly message: string;
}

interface SpeechRecognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
  onend: ((this: SpeechRecognition, ev: Event) => void) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition: { new(): SpeechRecognition };
    webkitSpeechRecognition: { new(): SpeechRecognition };
  }
}

export type TutorStatus =
  | "idle"
  | "listening"
  | "processing"
  | "answered"
  | "error";

export interface TutorMessage {
  role: "student" | "tutor";
  text: string;
  hint?: string | null;
}

interface UseTutorOptions {
  /** Current module context for API call */
  moduleId?: string;
  /** Active formula/element context */
  contextElementId?: string;
}

interface UseTutorResult {
  isOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
  status: TutorStatus;
  messages: TutorMessage[];
  transcript: string;
  setTranscript: (t: string) => void;
  liveAnnouncement: string;
  isSpeechSupported: boolean;
  /** MediaRecorder available — backend STT fallback usable */
  isRecorderSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  submitQuestion: () => Promise<void>;
  clearConversation: () => void;
}

export function useTutor(options: UseTutorOptions = {}): UseTutorResult {
  const { moduleId = "unknown", contextElementId = "general" } = options;

  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState<TutorStatus>("idle");
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [transcript, setTranscript] = useState("");
  const [liveAnnouncement, setLiveAnnouncement] = useState("");

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Check Web Speech API availability (Chrome, Safari, Edge)
  const isSpeechSupported =
    typeof window !== "undefined" &&
    ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);

  // Check MediaRecorder availability (fallback for Firefox)
  const isRecorderSupported =
    typeof window !== "undefined" && "MediaRecorder" in window;

  // ── Open / close ────────────────────────────────────────────────────────────

  const openModal = useCallback(() => {
    setIsOpen(true);
    setStatus("idle");
    setLiveAnnouncement("Tutor Sokrates terbuka. Ketik atau tekan Rekam untuk bertanya.");
  }, []);

  const closeModal = useCallback(() => {
    recognitionRef.current?.stop();
    if (mediaRecorderRef.current?.state !== "inactive") {
      mediaRecorderRef.current?.stop();
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
    setIsOpen(false);
    setStatus("idle");
    setTranscript("");
    setLiveAnnouncement("Tutor ditutup.");
  }, []);

  // Alt+T global shortcut
  useGlobalShortcut({
    key: "t",
    altKey: true,
    onTrigger: openModal,
  });

  // ── Web Speech API ──────────────────────────────────────────────────────────

  const startListening = useCallback(() => {
    // ── Branch 1: Web Speech API (Chrome/Safari/Edge) ──────────────────────
    if (isSpeechSupported) {
      const SpeechRecognitionImpl =
        window.SpeechRecognition ?? window.webkitSpeechRecognition;
      const recognition = new SpeechRecognitionImpl();
      recognitionRef.current = recognition;

      recognition.lang = "id-ID";
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onstart = () => {
        setStatus("listening");
        setTranscript("");
        setLiveAnnouncement("Merekam. Bicara sekarang.");
        earconRecordStart();
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interim = "";
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript;
          if (event.results[i].isFinal) final += t;
          else interim += t;
        }
        setTranscript(final || interim);
      };

      recognition.onend = () => {
        earconRecordStop();
        setStatus((prev) => (prev === "listening" ? "idle" : prev));
        setLiveAnnouncement("Rekaman selesai.");
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        earconError();
        setStatus("error");
        const msg =
          event.error === "not-allowed"
            ? "Izin mikrofon ditolak. Aktifkan izin mikrofon di browser Anda."
            : "Gagal merekam. Coba ketik pertanyaanmu.";
        setLiveAnnouncement(msg);
      };

      recognition.start();
      return;
    }

    // ── Branch 2: MediaRecorder + backend faster-whisper (Firefox fallback) ─
    if (!isRecorderSupported) {
      setLiveAnnouncement("Browser tidak mendukung input suara. Ketik pertanyaanmu.");
      return;
    }

    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        const chunks: Blob[] = [];
        audioChunksRef.current = chunks;

        // Prefer audio/webm (Firefox), fallback to audio/ogg
        const mimeType = MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "audio/ogg";

        const recorder = new MediaRecorder(stream, { mimeType });
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunks.push(e.data);
        };

        recorder.onstart = () => {
          setStatus("listening");
          setTranscript("");
          setLiveAnnouncement("Merekam. Bicara sekarang, lalu tekan stop.");
          earconRecordStart();
        };

        recorder.onstop = async () => {
          // Stop all tracks to release microphone
          stream.getTracks().forEach((t) => t.stop());
          earconRecordStop();
          setLiveAnnouncement("Rekaman selesai. Mengirim ke server…");
          setStatus("processing");

          const audioBlob = new Blob(chunks, { type: mimeType });
          const filename = mimeType === "audio/webm" ? "recording.webm" : "recording.ogg";

          try {
            const { transcript: text } = await transcribeAudio(audioBlob, filename);
            if (text.trim()) {
              setTranscript(text.trim());
              setStatus("idle");
              setLiveAnnouncement(`Terdeteksi: ${text.trim()}`);
            } else {
              setStatus("idle");
              setLiveAnnouncement("Tidak ada suara terdeteksi. Coba lagi.");
            }
          } catch {
            earconError();
            setStatus("error");
            setLiveAnnouncement("Transkripsi gagal. Coba ketik pertanyaanmu.");
          }
        };

        recorder.onerror = () => {
          earconError();
          setStatus("error");
          setLiveAnnouncement("Gagal merekam suara.");
        };

        recorder.start();
      })
      .catch(() => {
        earconError();
        setStatus("error");
        setLiveAnnouncement("Izin mikrofon ditolak. Aktifkan izin mikrofon di browser Anda.");
      });
  }, [isSpeechSupported, isRecorderSupported]);

  const stopListening = useCallback(() => {
    // Stop Web Speech API
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    // Stop MediaRecorder (triggers onstop → backend transcribe)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  // ── Submit question ─────────────────────────────────────────────────────────

  const submitQuestion = useCallback(async () => {
    const question = transcript.trim();
    if (!question) {
      setLiveAnnouncement("Pertanyaan kosong. Silakan ketik atau rekam pertanyaan.");
      return;
    }

    // Stop any active recording
    recognitionRef.current?.stop();

    // Add student message to conversation
    setMessages((prev) => [...prev, { role: "student", text: question }]);
    setTranscript("");
    setStatus("processing");
    setLiveAnnouncement("Tutor sedang menjawab…");

    try {
      const response = await askTutor({
        moduleId,
        contextElementId,
        transcriptText: question,
      });

      const tutorMsg: TutorMessage = {
        role: "tutor",
        text: response.answerText,
        hint: response.followUpHint,
      };

      setMessages((prev) => [...prev, tutorMsg]);
      setStatus("answered");
      earconResponseReady();
      setLiveAnnouncement(
        `Tutor menjawab: ${response.answerText}` +
          (response.followUpHint ? ` ${response.followUpHint}` : "")
      );
    } catch {
      setStatus("error");
      earconError();
      const errMsg = "Tutor tidak dapat menjawab saat ini. Coba lagi.";
      setMessages((prev) => [...prev, { role: "tutor", text: errMsg }]);
      setLiveAnnouncement(errMsg);
    }
  }, [transcript, moduleId, contextElementId]);

  // ── Clear conversation ──────────────────────────────────────────────────────

  const clearConversation = useCallback(() => {
    setMessages([]);
    setStatus("idle");
    setTranscript("");
    setLiveAnnouncement("Percakapan dihapus.");
  }, []);

  return {
    isOpen,
    openModal,
    closeModal,
    status,
    messages,
    transcript,
    setTranscript,
    liveAnnouncement,
    isSpeechSupported,
    isRecorderSupported,
    startListening,
    stopListening,
    submitQuestion,
    clearConversation,
  };
}
