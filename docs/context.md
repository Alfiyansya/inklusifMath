# InklusifMath — AI Context Document

> **Last Updated:** 2026-09-20 13:30
> **Branch:** `main`
> **Latest Commit:** `8b235e5` (UI/UX — uncommitted changes banyak, perlu commit)
> **Backend Tests:** 281 passed · **Frontend TypeScript:** 0 errors

---

## 1. Apa Itu InklusifMath?

Platform e-learning matematika yang **aksesibel untuk siswa tunanetra** di Indonesia. Guru mengunggah modul (.docx/.pdf), sistem AI mengekstraksi rumus matematika, membangkitkan narasi verbal Bahasa Indonesia, lalu menerbitkan modul yang bisa dibaca screen reader. Ada juga Tutor AI Sokrates yang bisa ditanya siswa via push-to-talk.

**Target compliance:** WCAG 2.2 AA, WAI-ARIA 1.2

---

## 2. Tech Stack (Final)

| Layer | Teknologi | Versi |
|-------|-----------|-------|
| **Frontend** | Next.js (App Router) + TypeScript | 16.3.5 |
| **Styling** | Tailwind CSS v4 + CSS custom properties | 4.x |
| **A11y UI** | React Aria Components | 1.21.1 |
| **Math Rendering** | MathJax (CDN lazy-load) | 3.2.1 |
| **Frontend Testing** | Vitest 5.0 + @testing-library/react + Playwright | — |
| **Backend** | FastAPI + SQLAlchemy 2.0 (async) | 0.115+ |
| **Database** | PostgreSQL 16 | 16 |
| **Cache / Queue** | Redis 7 | 7 |
| **Auth** | Firebase Auth (Email/Password) | firebase@11.x |
| **User Profiles** | Firebase Firestore | — |
| **Auth Backend** | firebase-admin (token verification) | 7.5.0 |
| **AI** | Google Gemini 2.0 Flash (narasi + tutor) | google-genai |
| **OCR** | Google Cloud Vision + Mathpix | google-cloud-vision≥3.8 |
| **STT** | Web Speech API (primary) + faster-whisper (fallback) | — |
| **PDF** | PyMuPDF (fitz) + pdfplumber | — |
| **DOCX** | python-docx | — |
| **Python** | 3.14 | 3.14.7 |
| **Migration** | Alembic (async) | — |
| **CI** | GitHub Actions | — |

---

## 3. Firebase Configuration

| Item | Value |
|------|-------|
| **Project ID** | `inklusifmath-6d7e9` |
| **Web App ID** | `1:699742854764:web:137aac4603661afb408249` |
| **Auth Provider** | Email/Password (enabled) |
| **Firestore DB** | `(default)` — `asia-southeast2` |
| **Firestore Collection** | `users/{uid}` — stores role, fullName, email, studentLevel |
| **Firebase Account** | `alfiansyahsecond@gmail.com` |

### Auth Flow

```
Register: Frontend → Firebase Auth → Firestore users/{uid} → redirect by role
Login:    Frontend → Firebase Auth → Firestore (read role) → redirect
API:      Frontend → user.getIdToken() → Authorization: Bearer {token}
          Backend  → firebase-admin verify_id_token() → decoded claims
```

### Firestore Schema (`users/{uid}`)

```
role:         'teacher' | 'student' | 'admin'
fullName:     string
email:        string
studentLevel: 'SD' | 'SMP' | 'SMA' | null   (students only)
createdAt:    timestamp
```

### Env Vars — Frontend (`.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyDUAXq7VX4McyGs6vtW1H9tq_oI6X8FDSE
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=inklusifmath-6d7e9.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=inklusifmath-6d7e9
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=inklusifmath-6d7e9.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=699742854764
NEXT_PUBLIC_FIREBASE_APP_ID=1:699742854764:web:137aac4603661afb408249
```

Template: `frontend/.env.example`

### Env Vars — Backend (`.env`)

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/inklusifmath
REDIS_URL=redis://localhost:6379/0
FIREBASE_PROJECT_ID=inklusifmath-6d7e9
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-2.0-flash
GCV_OCR_ENABLED=true                        # false to skip OCR
GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
MATHPIX_ENABLED=true
MATHPIX_APP_ID=<your-id>
MATHPIX_APP_KEY=<your-key>
MAX_UPLOAD_SIZE_MB=20
UPLOAD_DIR=uploads
CORS_ORIGINS=["http://localhost:3000"]
```

Template: `backend/.env.example`

---

## 4. Project Structure

```
inklusifMath/
├── docs/
│   ├── context.md                    # ← THIS FILE (AI ground truth)
│   ├── prd_ai_friendly_inklusifmath.md
│   ├── srs_inklusifmath.md
│   ├── tdd_inklusifmath.md
│   └── leksikon_matematika_baku.md   # 50+ entri narasi matematika baku
│
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI entry: CORS, rate limiter, Firebase init
│   │   ├── core/
│   │   │   ├── config.py             # Pydantic Settings (semua env vars)
│   │   │   ├── database.py           # SQLAlchemy 2.0 async engine + session
│   │   │   ├── firebase.py           # ✅ Firebase Admin SDK + verify_firebase_token()
│   │   │   ├── dependencies.py       # ✅ get_current_user(), require_role()
│   │   │   └── rate_limiter.py       # slowapi Limiter (Redis backend)
│   │   ├── models/
│   │   │   ├── __init__.py           # ⚠ MUST import ALL models (SQLAlchemy relationships)
│   │   │   ├── user.py               # User (id, firebase_uid, email, role, full_name, student_level)
│   │   │   ├── document.py           # Document, MathExpression, LearningModule
│   │   │   └── tutor.py              # TutorSession, TutorMessage
│   │   ├── schemas/
│   │   │   ├── auth.py               # ProfileCreateRequest, UserResponse
│   │   │   ├── document.py           # Upload/Status/List/Detail/Narration/Approve schemas
│   │   │   ├── module.py             # ModuleListItem, ModuleDetail, ModulePublishRequest/Response
│   │   │   └── tutor.py              # TutorAskRequest, TutorAskResponse
│   │   ├── api/v1/
│   │   │   ├── router.py
│   │   │   └── endpoints/
│   │   │       ├── auth.py           # ✅ POST /profile, GET /me, POST /logout
│   │   │       ├── documents.py      # ✅ GET /documents, GET /{id}, POST /upload,
│   │   │       │                     #      GET /{id}/status, GET /{id}/narrations,
│   │   │       │                     #      PATCH /narrations/{id}, POST /{id}/approve
│   │   │       ├── modules.py        # ✅ GET /modules, GET /modules/{id}, POST /modules/{id}/publish
│   │   │       ├── tutor.py          # ✅ POST /tutor/ask (Gemini Socratic)
│   │   │       └── stt.py            # ✅ POST /stt/transcribe (faster-whisper fallback)
│   │   └── services/
│   │       ├── document_service.py   # ✅ Full: create, parse, save, narrate, list, detail,
│   │       │                         #      approve, toggle_module_publish, run_ocr_if_needed
│   │       ├── tutor_service.py      # ✅ ask_tutor() — Gemini 2.0 Flash + Socratic prompt
│   │       ├── stt_service.py        # ✅ faster-whisper tiny CPU int8, lazy singleton
│   │       ├── ai/
│   │       │   ├── clarifier.py      # ✅ AiClarifier — Gemini batch narration + retry
│   │       │   └── leksikon.py       # ✅ Leksikon Matematika Baku system prompts
│   │       ├── parsing/
│   │       │   ├── models.py         # ParsedDocument, ContentBlock, MathExpressionResult
│   │       │   ├── docx_parser.py    # ✅ DocxParser — heading/para/table + OMML math
│   │       │   ├── pdf_parser.py     # ✅ PdfParser — font heuristic + 7 math patterns
│   │       │   └── omml_to_latex.py  # ✅ OMML → LaTeX (14 constructs)
│   │       └── ocr/
│   │           ├── __init__.py
│   │           ├── gcv_service.py    # ✅ GcvOcrService — DOCUMENT_TEXT_DETECTION 300DPI
│   │           ├── mathpix_service.py# ✅ MathpixService — image→LaTeX, confidence≥0.5
│   │           └── ocr_pipeline.py   # ✅ Orchestrator GCV+Mathpix → ParsedDocument
│   ├── alembic/versions/
│   │   ├── 850d2a6c7593_initial_schema.py
│   │   ├── bf496f6764d6_fix_datetime_to_timestamptz.py
│   │   ├── c3a7f1e82d4a_add_student_level_to_users.py
│   │   ├── d5e8f2a91b3c_add_firebase_uid.py
│   │   └── e1f9a3b04c2d_add_performance_indexes.py   # 6 composite indexes
│   ├── tests/                        # 281 tests total (all --noconftest)
│   │   ├── test_health.py / test_auth.py  # 9 tests (need DB conftest — ignore in --noconftest)
│   │   ├── test_docx_parser.py       # 27 tests
│   │   ├── test_pdf_parser.py        # 34 tests
│   │   ├── test_document_service.py  # 83 tests
│   │   ├── test_document_listing.py  # 17 tests (GET /documents + GET /{id})
│   │   ├── test_modules.py           # 11 tests
│   │   ├── test_toggle_publish.py    # 17 tests (POST /modules/{id}/publish)
│   │   ├── test_ai_clarifier.py      # 36 tests
│   │   ├── test_tutor.py             # 14 tests
│   │   ├── test_stt.py               # 14 tests
│   │   ├── test_ocr_pipeline.py      # 32 tests
│   │   ├── test_error_handling.py    # 37 tests
│   │   └── test_sql_indexes.py       # 25 tests
│   ├── requirements.txt              # Semua deps dengan min version pins
│   ├── .env.example                  # ✅ Template env vars dengan komentar
│   └── pyproject.toml                # pytest-asyncio: session loop scope
│
├── frontend/
│   ├── src/app/
│   │   ├── layout.tsx                # Root layout (Inter + Poppins, lang="id", AuthProvider)
│   │   ├── globals.css               # 14 CSS custom properties (design tokens)
│   │   ├── login/page.tsx            # ✅ Firebase Auth login
│   │   ├── register/page.tsx         # ✅ Multi-step register
│   │   ├── dashboard/
│   │   │   ├── layout.tsx            # ✅ Auth guard + role routing
│   │   │   ├── page.tsx              # ✅ Guru dashboard: "Dokumen Saya" + "Modul Terbit"
│   │   │   └── student/page.tsx      # ✅ Siswa dashboard: modul list + tutor shortcut
│   │   ├── upload/
│   │   │   ├── page.tsx              # ✅ Upload DOCX/PDF drag-and-drop
│   │   │   └── [id]/review/page.tsx  # ✅ Review narasi 2-kolom + approve
│   │   ├── modules/
│   │   │   ├── page.tsx              # ✅ Daftar modul siswa (ModuleCard + aria)
│   │   │   └── [id]/page.tsx         # ✅ Baca modul: Formula Gallery + J/K nav + TutorModal
│   ├── src/components/
│   │   ├── auth/                     # AuthBranding, AuthCard
│   │   ├── layout/Header.tsx         # ✅ Dual variant: guru / siswa (Alt+T)
│   │   ├── math/
│   │   │   ├── MathRenderer.tsx      # ✅ aria-label override, MathJax speech disabled
│   │   │   └── MathDisplay.tsx       # ✅ Dual-layer: visual + narasi Indonesia
│   │   ├── tutor/
│   │   │   └── TutorModal.tsx        # ✅ role="dialog" + focus trap + createPortal
│   │   └── ui/
│   │       ├── SkipLink.tsx          # ✅ WCAG 2.4.1
│   │       ├── LiveRegion.tsx        # ✅ aria-live polite + assertive
│   │       ├── ApiStatusBanner.tsx   # ✅ Banner mock data mode
│   │       └── ...
│   ├── src/hooks/
│   │   ├── useFocusRestore.ts        # Focus save/restore untuk modal
│   │   ├── useGlobalShortcut.ts      # Global keydown (Alt+T)
│   │   ├── useModules.ts             # ✅ GET /modules + fallback mock
│   │   ├── useDocuments.ts           # ✅ GET /documents + fallback mock (baru)
│   │   ├── useNarrations.ts          # ✅ GET/PATCH narrations + approve
│   │   ├── useDocumentUpload.ts      # ✅ POST /documents/upload
│   │   └── useTutor.ts               # ✅ Web Speech API + POST /tutor/ask + earcon
│   ├── src/lib/
│   │   ├── firebase.ts               # ✅ Firebase App + Auth + Firestore init
│   │   ├── firestore.ts              # ✅ createUserProfile() + getUserProfile()
│   │   ├── api/
│   │   │   ├── client.ts             # ✅ Fetch wrapper + Firebase token auto-attach
│   │   │   ├── documents.ts          # ✅ upload, narrations, update, approve,
│   │   │   │                         #    fetchDocumentList(), fetchDocumentDetail() (baru)
│   │   │   └── modules.ts            # ✅ fetchModules(), fetchModuleDetail()
│   │   └── audio/earcon.ts           # ✅ 5 suara sintetis Web Audio API (<15ms)
│   ├── src/test/setup.ts             # jest-dom setup untuk Vitest
│   ├── src/lib/api/__tests__/
│   │   ├── client.test.ts            # 7 tests
│   │   ├── modules.test.ts           # 12 tests
│   │   └── documents.test.ts         # 16 tests (10 lama + 6 baru list/detail)
│   ├── e2e/                          # Playwright E2E tests
│   │   ├── fixtures.ts               # Shared mocks + helpers
│   │   ├── homepage.spec.ts          # 6 tests
│   │   ├── login.spec.ts             # 7 tests
│   │   ├── modules.spec.ts           # 5 tests
│   │   ├── module-reader.spec.ts     # 7 tests
│   │   └── accessibility.spec.ts     # 13 tests × 3 pages
│   ├── vitest.config.ts              # jsdom, @vitejs/plugin-react, @/* alias
│   ├── playwright.config.ts          # Chromium + Firefox, webServer auto-start
│   └── .env.example                  # ✅ Template env vars
│
├── docker-compose.yml                # PostgreSQL 16 + Redis 7
├── .github/workflows/ci.yml          # backend pytest + frontend build + Lighthouse
├── firestore.rules                   # Users can only read/write own doc
└── README.md
```

---

## 5. Database Schema (6 Tables)

```
users
  id            UUID PK
  firebase_uid  VARCHAR(128) UNIQUE INDEX
  email         VARCHAR(255) UNIQUE
  role          VARCHAR(20)   -- 'teacher' | 'student' | 'admin'
  student_level VARCHAR(10) NULLABLE   -- 'SD' | 'SMP' | 'SMA'
  full_name     VARCHAR(255)
  created_at / updated_at  TIMESTAMPTZ

documents
  id                UUID PK
  teacher_id        UUID FK → users.id
  title             VARCHAR(500)
  file_type         VARCHAR(10)    -- 'docx' | 'pdf'
  original_file_path TEXT
  parsing_status    VARCHAR(20)   -- 'pending'|'processing'|'parsed'|'failed'
  ocr_used          VARCHAR(20)   -- 'none'|'pending_ocr'|'gcv'|'gcv+mathpix'
  raw_structure     JSONB          -- includes math_count
  error_code        VARCHAR(20) NULLABLE   -- PARSE_001, DOC_001, etc.
  created_at / updated_at TIMESTAMPTZ

math_expressions
  id                  UUID PK
  document_id         UUID FK → documents.id
  original_notation   TEXT
  latex_representation TEXT
  ai_narration        TEXT NULLABLE
  teacher_narration   TEXT NULLABLE
  status              VARCHAR(20)   -- 'pending'|'ai_generated'|'reviewed'|'approved'
  position_order      INTEGER
  created_at          TIMESTAMPTZ

learning_modules
  id            UUID PK
  document_id   UUID FK → documents.id (UNIQUE)
  html_content  TEXT
  is_published  BOOLEAN DEFAULT FALSE
  published_at  TIMESTAMPTZ NULLABLE
  approved_by   UUID FK → users.id NULLABLE

tutor_sessions
  id                  UUID PK
  student_id          UUID FK → users.id
  module_id           UUID FK → learning_modules.id
  context_element_id  VARCHAR(100)
  started_at / ended_at TIMESTAMPTZ

tutor_messages
  id          UUID PK
  session_id  UUID FK → tutor_sessions.id
  role        VARCHAR(10)   -- 'user' | 'assistant'
  content     TEXT
  created_at  TIMESTAMPTZ
```

### Performance Indexes (Alembic: `e1f9a3b04c2d`)

```sql
ix_documents_teacher_created        (teacher_id, created_at)        -- guru listing
ix_math_expressions_doc_position    (document_id, position_order)   -- narasi review order
ix_math_expressions_doc_status      (document_id, status)           -- publish gate
ix_learning_modules_published_at    (is_published, published_at)    -- siswa listing
ix_tutor_sessions_student_module    (student_id, module_id)         -- session lookup
ix_tutor_messages_session_created   (session_id, created_at)        -- chat history
```

---

## 6. API Endpoints (Semua ✅ Implemented)

| Method | Endpoint | Rate Limit | Auth | Keterangan |
|--------|----------|-----------|------|------------|
| GET | `/health` | — | No | Health check |
| POST | `/api/v1/auth/profile` | 5/hr | Firebase | Sync profil ke PostgreSQL |
| GET | `/api/v1/auth/me` | 60/min | Firebase | Data user terautentikasi |
| POST | `/api/v1/auth/logout` | 10/min | Firebase | Client-side signout |
| **GET** | **`/api/v1/documents`** | 60/min | Teacher | List dokumen guru, newest-first, pagination |
| **GET** | **`/api/v1/documents/{id}`** | 60/min | Teacher | Detail + narration 4-bucket progress |
| POST | `/api/v1/documents/upload` | 10/hr | Teacher | Upload + parse + AI narasi |
| GET | `/api/v1/documents/{id}/status` | 120/min | Teacher | Parsing status |
| **GET** | **`/api/v1/documents/{id}/progress`** | 60/min | Teacher | SSE stream parsing progress (ADR-006) |
| GET | `/api/v1/documents/{id}/narrations` | 60/min | Teacher | Semua MathExpression sorted |
| PATCH | `/api/v1/narrations/{id}` | 120/hr | Teacher | Edit narasi guru |
| POST | `/api/v1/documents/{id}/approve` | 20/hr | Teacher | Approve + publish module |
| GET | `/api/v1/modules` | 60/min | Any | Modul published, siswa listing |
| GET | `/api/v1/modules/{id}` | 120/min | Any | Detail modul + MathExpression |
| **POST** | **`/api/v1/modules/{id}/publish`** | 10/hr | Teacher | Toggle is_published (publish/unpublish) |
| POST | `/api/v1/tutor/ask` | 30/hr | Student/Admin | Gemini 2.0 Flash Socratic |
| POST | `/api/v1/stt/transcribe` | 20/hr | Any | faster-whisper fallback STT |

> **Bold** = endpoints yang baru dibuat di sesi ini (Sept 20, 2026).
> Tidak ada endpoint stub/501 yang tersisa.

---

## 7. Upload Pipeline (Full Flow)

```
POST /documents/upload
  1. Validate MIME (docx/pdf) + size (≤20MB) + not empty
  2. Read bytes into memory
  3. Save to UPLOAD_DIR (aiofiles)
  4. Create Document(status='processing') in DB
  5. parse_document() in thread pool (CPU-bound)
     ├── DOCX → DocxParser (heading + OMML math)
     └── PDF  → PdfParser  (font heuristic + 7 math patterns)
                 ↓ if scanned → ocr_used='pending_ocr'
  6. run_ocr_if_needed(file_bytes, parsed, title)  ← NEW
     ├── if ocr_used != 'pending_ocr' → skip (return as-is)
     └── if pending_ocr:
         ├── GcvOcrService.extract_text_from_pdf() [DOCUMENT_TEXT_DETECTION, 300DPI]
         ├── _gcv_text_to_parsed_document()  → ParsedDocument(ocr_used='gcv')
         ├── _extract_math_image_regions()   → crop math image regions
         ├── MathpixService.images_to_latex_batch() [confidence≥0.5, semaphore(3)]
         └── Merge Mathpix LaTeX → ParsedDocument(ocr_used='gcv+mathpix')
             Graceful fallback: if GCV fails → stays 'pending_ocr' (teacher handles)
  7. save_math_expressions() → MathExpression rows in DB
  8. generate_ai_narrations() [best-effort, non-fatal]
     └── AiClarifier → Gemini 2.0 Flash batch(20) + Leksikon Baku system prompt
  9. update_document_after_parse() → parsing_status='parsed', raw_structure
  → Response 202: {document_id, title, status, math_count, ocr_used, message}
```

---

## 8. Frontend Architecture

### CSS Gotcha (CRITICAL)
```tsx
// ✅ CORRECT — semua komponen wajib gunakan ini
style={{ color: "var(--color-primary)" }}

// ❌ WRONG — Turbopack crashes dengan Tailwind v4 custom colors
className="text-primary"
```

### Design Tokens (CSS Custom Properties in `globals.css`)

```css
--color-primary:        #6495ED   /* Cornflower blue */
--color-primary-hover:  #5280D8
--color-bg-page:        #F0F5FF
--color-bg-card:        #FFFFFF
--color-border-card:    #C8DCFA
--color-text-primary:   #1F2A44
--color-text-secondary: #5A6A8A
--color-text-muted:     #8A9ABB
--color-success:        #10B981
--color-warning:        #F59E0B
--color-tag-bg:         #EAF3FF
--color-tag-text:       #6495ED
--color-avatar-bg:      #EAF3FF
```

### Key Frontend Patterns

```typescript
// API client — auto-attach Firebase token
import { apiRequest } from "@/lib/api/client";
const data = await apiRequest<ResponseType>("/endpoint", { method: "POST", body: ... });

// Hook pattern (useDocuments, useModules, useNarrations)
const { documents, total, isLoading, isUsingMockData, refetch } = useDocuments();
// isUsingMockData=true → show <ApiStatusBanner />

// Tutor — Alt+T shortcut
useGlobalShortcut({ key: "t", altKey: true }, openTutor);

// STT — Web Speech API primary, faster-whisper fallback untuk Firefox
// SpeechRecognition → transcript → POST /tutor/ask
// MediaRecorder → POST /stt/transcribe → transcript → POST /tutor/ask

// Math rendering — dual-layer (WCAG accessible)
<MathDisplay latex={expr.latex} narration={narration} />
// MathJax visual (sighted) + aria-label narasi Indonesia (screen reader)
```

---

## 9. Accessibility (WCAG 2.2 AA)

| Feature | Implementasi |
|---------|-------------|
| Skip Link | `SkipLink.tsx` — "Langsung ke konten utama" |
| Live Region | `LiveRegion.tsx` — polite + assertive |
| Focus Trap | `TutorModal.tsx` — Tab/Shift+Tab cycling, Escape closes |
| Focus Restore | `useFocusRestore.ts` — simpan & kembalikan focus setelah modal |
| Global Shortcut | `Alt + T` → buka TutorModal |
| Dual-Layer Math | MathJax visual + `aria-label` narasi Indonesia (MathJax speech disabled) |
| Heading Structure | h1 per halaman, h2/h3 dari html_content modul |
| Earcon | 5 suara sintetis Web Audio API < 15ms latency |
| Zero Audio Collision | Tidak ada TTS web — platform mengandalkan screen reader native |
| Keyboard Nav | J/K untuk navigate formula di `/modules/[id]` |

---

## 10. Testing

### Backend (run tanpa DB)

```bash
cd backend && .venv/bin/python -m pytest \
  tests/test_docx_parser.py tests/test_pdf_parser.py \
  tests/test_document_service.py tests/test_document_listing.py \
  tests/test_modules.py tests/test_toggle_publish.py \
  tests/test_ai_clarifier.py tests/test_tutor.py tests/test_stt.py \
  tests/test_ocr_pipeline.py tests/test_error_handling.py tests/test_sql_indexes.py \
  --noconftest -v
# Result: 281 passed
```

> **⚠ test_auth.py + test_health.py** — perlu DB + Firebase conftest. Jalankan `docker compose up -d` dulu. 9 tests yang ini adalah pre-existing, bukan dari kode baru.

### Frontend

```bash
# Unit tests (Vitest)
cd frontend && npm test
# Result: 35 tests — client(7) + modules(12) + documents(16)

# TypeScript check
cd frontend && npx tsc --noEmit
# Result: 0 errors

# E2E (perlu dev server jalan)
cd frontend && npx playwright test
# 5 spec files: homepage(6) + login(7) + modules(5) + reader(7) + a11y(13×3)
```

---

## 11. Error Handling Taxonomy

| Kode | Domain | HTTP | Pesan |
|------|--------|------|-------|
| `DOC_001` | Upload | 413 | File > 20MB |
| `DOC_002` | Upload | 415 | Format tidak didukung |
| `DOC_003` | Upload | 422 | File corrupt/kosong |
| `PARSE_001` | Parsing | 422 | Gagal ekstraksi teks |
| `PARSE_002` | Parsing | 422 | OCR fallback gagal |
| `PARSE_003` | Parsing | 200 | Tidak ada ekspresi matematika |
| `AI_001` | Clarifier | — | Gemini timeout → retry 2x |
| `AI_002` | Clarifier | — | Gemini down → graceful degradation |
| `AI_003` | Tutor | 503 | Gemini timeout → fallback pool |
| `STT_001` | STT | 503 | Model tidak tersedia |
| `STT_002` | STT | 422 | Audio kosong |
| `STT_003` | STT | 413 | File > 5MB |
| `TUTOR_001` | Tutor | 422 | Pertanyaan kosong |
| `AUTH_001/002` | Auth | — | Firebase handles token refresh |

---

## 12. Docker Services

```bash
docker compose up -d   # Start PostgreSQL + Redis
```

| Service | Port | Container |
|---------|------|-----------|
| PostgreSQL 16 | 5432 | inklusifmath-db |
| Redis 7 | 6379 | inklusifmath-redis |

```bash
# Apply migrations
cd backend && alembic upgrade head
# Current head: e1f9a3b04c2d (add_performance_indexes)
```

---

## 13. Known Quirks & Gotchas

1. **Turbopack + `@theme inline`** — CRASHES. Wajib pakai `:root` CSS vars + `style={{}}`.
2. **`models/__init__.py`** — HARUS import semua model. SQLAlchemy string relationships fail kalau tidak.
3. **`asyncio_default_test_loop_scope = "session"`** — Wajib di `pyproject.toml`. Tanpa ini asyncpg connections break antar test.
4. **`DateTime(timezone=True)`** — Semua model datetime harus pakai ini. asyncpg reject offset-naive datetimes ke TIMESTAMPTZ.
5. **slowapi rate limiter** — `isinstance(request, Request)` dari starlette. Jangan gunakan `MagicMock()` untuk test endpoint rate-limited. Gunakan `Request(scope={"type":"http",...})` sungguhan.
6. **`_mock_request()` pattern** — Untuk test endpoint rate-limited: `from starlette.requests import Request; Request(scope={"type":"http","method":"GET","path":"/","query_string":b"","headers":[],"client":("127.0.0.1",9999)})`.
7. **Firebase init** — `init_firebase()` dipanggil di `main.py` lifespan. Pakai `GCLOUD_PROJECT` env var atau service account JSON.
8. **OCR credentials** — `GcvOcrService` pakai `GOOGLE_APPLICATION_CREDENTIALS` env var (sama dengan Firebase jika akun yang sama). Set `GCV_OCR_ENABLED=false` untuk skip di dev.
9. **`run_ocr_if_needed` adalah no-op** untuk dokumen non-scanned — safe untuk semua upload.
10. **Frontend build** — `next build` perlu network (Google Fonts). `next dev` aman tanpa network.

---

## 14. Sisa Pekerjaan (Open Items)

### High Priority
Semua high-priority item arsitektur (Celery Worker 5.11, GCS Storage 12.3, Deployment Config 12.4, SSE Progress 4.2.5, Granular RBAC 1.12, TutorModal & ModuleReader wiring 3.2.11/12) **telah selesai diimplementasikan**.

### Sisa Pekerjaan Terbuka
| Item | Keterangan |
|------|------------|
| **Math Term Normalization** (5.10) | "satu per dua" → `½` di output tutor |
| **PUT /narrations bulk** (4.2.8) | Bulk update semua narasi sekaligus (opsional, saat ini via PATCH per item) |
| Responsive layout audit (13.3) | Belum diverifikasi di mobile viewport |
| High-contrast focus indicators (13.4) | WCAG AA visual audit |

### Low Priority / Nice-to-Have
| Item | Keterangan |
|------|------------|
| Responsive layout audit (13.3) | Belum diverifikasi di mobile viewport |
| High-contrast focus indicators (13.4) | WCAG AA perlu audit |
| `aria-live` konsisten (6.15) | LiveRegion belum dipakai di semua konteks error |

---

## 15. Alembic Migration Chain

```
850d2a6c7593  →  bf496f6764d6  →  c3a7f1e82d4a  →  d5e8f2a91b3c  →  e1f9a3b04c2d (HEAD)
initial_schema   fix_timestamptz   student_level     firebase_uid      performance_indexes
```

---

## 16. Git History (belum di-commit sejak `8b235e5`)

Semua perubahan sejak 17 September 2026 belum di-commit. Perlu `git add -A && git commit`.

Perubahan besar yang belum di-commit:
- Backend: semua services (document_service, clarifier, tutor_service, stt_service, ocr/*)
- Backend: semua endpoints (documents, modules, tutor, stt) — semuanya sudah real
- Backend: schemas, alembic migration performance_indexes, 281 tests
- Frontend: semua halaman baru (modules, module-reader, upload/review), hooks, components
- Frontend: useDocuments hook, Vitest tests, Playwright E2E
- Docs: .env.example (backend + frontend), context.md ini
