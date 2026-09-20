"""
Tutor service — Gemini Socratic AI for math questions.

Implements ADR-002: Socratic method (tidak memberi jawaban langsung,
mendorong siswa berpikir kritis lewat pertanyaan pemandu).

Design:
  - Gemini 2.0 Flash untuk respons cepat (< 3s target)
  - System prompt Sokrates: TIDAK boleh langsung jawab, selalu tanya balik
  - Konteks: module_id + context_element_id (posisi siswa di modul)
  - Rate limit: 30/jam (enforcement di endpoint layer via slowapi)
  - Session tracking: TutorSession di DB (best-effort)
  - Error fallback: pesan ramah jika Gemini gagal
"""

from __future__ import annotations

import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)

# ── Socratic system prompt ────────────────────────────────────────────────────
# Berdasarkan TDD Section 8 (Tutor AI Sokrates)

SOCRATIC_SYSTEM_PROMPT = """Kamu adalah Tutor Sokrates untuk platform matematika inklusif InklusifMath.
Kamu membantu siswa tunanetra dan low-vision belajar matematika dengan metode Sokrates.

ATURAN MUTLAK:
1. JANGAN pernah langsung memberikan jawaban akhir. Selalu pandu dengan pertanyaan.
2. Gunakan Bahasa Indonesia yang ramah, jelas, dan mudah dimengerti siswa SD/SMP/SMA.
3. Respons SINGKAT: 2–4 kalimat maksimum. Siswa menggunakan screen reader, panjang teks melelahkan.
4. Selalu akhiri dengan pertanyaan pemandu yang mendorong siswa berpikir sendiri.
5. Jika siswa sudah dekat jawaban, beri pujian kecil lalu tanya langkah berikutnya.
6. Jika pertanyaan di luar matematika, minta siswa fokus ke materi modul dengan ramah.
7. Gunakan analogi sehari-hari yang konkret untuk membantu pemahaman.
8. JANGAN gunakan simbol matematika raw (LaTeX). Ejakan dengan kata: "dua pangkat tiga", "pecahan satu per dua".

GAYA RESPONS:
- Hangat, supportif, sabar
- Pujian kecil: "Pertanyaan bagus!", "Kamu sudah berpikir dengan benar."
- Pertanyaan pemandu: "Coba pikirkan...", "Apa yang terjadi jika...", "Menurutmu, mengapa..."

KONTEKS: Kamu ada di halaman modul matematika. Siswa baru saja menemukan rumus atau konsep
yang membingungkan dan membutuhkan bantuan untuk memahaminya secara mandiri."""

# ── Fallback responses ────────────────────────────────────────────────────────

FALLBACK_RESPONSES = [
    "Pertanyaan menarik! Coba pikirkan dulu — apa yang sudah kamu ketahui tentang topik ini? Langkah kecil pertama biasanya yang paling penting.",
    "Bagus kamu bertanya! Sebelum saya bantu, coba ceritakan apa yang membuatmu bingung? Dengan begitu saya bisa membimbingmu lebih baik.",
    "Saya senang kamu mau belajar! Mari kita pecah masalah ini satu langkah demi satu. Apa bagian yang paling membingungkan bagimu?",
]

_fallback_idx = 0


def _get_fallback() -> str:
    global _fallback_idx
    msg = FALLBACK_RESPONSES[_fallback_idx % len(FALLBACK_RESPONSES)]
    _fallback_idx += 1
    return msg


# ── Main function ─────────────────────────────────────────────────────────────

_TUTOR_TIMEOUT_SECONDS = 20  # AI_003: tutor must respond quickly (screen reader UX)


async def ask_tutor(
    question: str,
    module_id: str,
    context_element_id: str,
) -> tuple[str, str | None]:
    """
    Ask the Socratic tutor a question.

    Returns:
        (answer_text, follow_up_hint)
        answer_text: main Socratic response
        follow_up_hint: optional next question hint (may be None)

    Error handling:
        - AI_003: Gemini timeout > 20s → returns fallback message (never raises)
        - Any other error → returns fallback message (never raises)
    """
    from app.core.config import settings

    prompt_text = (
        f"[Konteks modul: {module_id} | elemen: {context_element_id}]\n\n"
        f"Pertanyaan siswa: {question}"
    )

    try:
        # Lazy import — avoid import-time API key check
        import google.genai as genai
        import google.genai.types as genai_types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # AI_003: wrap Gemini call with timeout
        loop = asyncio.get_running_loop()
        async with asyncio.timeout(_TUTOR_TIMEOUT_SECONDS):
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt_text,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=SOCRATIC_SYSTEM_PROMPT,
                        temperature=0.7,          # Sedikit kreatif untuk variasi respons
                        max_output_tokens=300,    # Singkat — screen reader friendly
                        safety_settings=[
                            genai_types.SafetySetting(
                                category="HARM_CATEGORY_HATE_SPEECH",
                                threshold="BLOCK_ONLY_HIGH",
                            ),
                            genai_types.SafetySetting(
                                category="HARM_CATEGORY_HARASSMENT",
                                threshold="BLOCK_ONLY_HIGH",
                            ),
                        ],
                    ),
                ),
            )

        answer = response.text.strip() if response.text else _get_fallback()

        # Extract follow-up hint: last sentence ending with "?"
        sentences = [s.strip() for s in answer.split(".") if s.strip()]
        follow_up = None
        for s in reversed(sentences):
            if s.endswith("?"):
                follow_up = s + "?"
                break

        return answer, follow_up

    except TimeoutError:
        # AI_003: Gemini did not respond in time
        logger.warning(
            "[AI_003] Tutor Gemini timeout after %ds — using fallback",
            _TUTOR_TIMEOUT_SECONDS,
        )
        fallback = _get_fallback()
        return fallback, None

    except Exception as exc:
        logger.warning(
            "[tutor_service] Gemini gagal: %s — menggunakan fallback",
            exc,
            exc_info=False,
        )
        fallback = _get_fallback()
        return fallback, None
