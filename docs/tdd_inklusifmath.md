# Technical Design Document (TDD)
## InklusifMath Platform
### Versi 1.0 — Diturunkan dari PRD v2.0-draft dan SRS v1.0

---

## 1. Metadata Dokumen

- **Nama produk:** InklusifMath Platform
- **Jenis dokumen:** Technical Design Document (TDD)
- **Versi dokumen:** 1.0
- **Status:** Approved
- **Tanggal:** 2026-09-16
- **Dokumen sumber:**
  - `prd_ai_friendly_inklusifmath.md` (PRD v2.0-draft)
  - `srs_inklusifmath.md` (SRS v1.0)

---

## 2. Ringkasan Arsitektur

InklusifMath Platform menggunakan arsitektur **decoupled frontend-backend** dengan komunikasi melalui REST API (HTTPS). Frontend dirender secara server-side untuk memenuhi target First Contentful Paint < 1.5 detik dan kompatibilitas optimal dengan screen reader native.

### 2.1 Diagram Arsitektur Tingkat Tinggi

```
┌──────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│                   Next.js 14+ (App Router)                   │
│                     Deployed: Vercel                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Portal Guru  │  │ Modul Siswa  │  │   Dialog Tutor     │  │
│  │  - Upload    │  │  - Heading   │  │  - Push-to-Talk    │  │
│  │  - Review    │  │  - Math Dual │  │  - Live Region     │  │
│  │  - Approve   │  │    Layer     │  │  - Focus Trap      │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
│                                                              │
│  Libraries: React Aria, MathJax 4, TypeScript, Tailwind CSS  │
│  APIs: Web Audio API (earcon), MediaDevices API (voice)      │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTPS (REST API + SSE)
┌──────────────────────────┴───────────────────────────────────┐
│                         BACKEND                              │
│                   Python FastAPI                             │
│                  Deployed: Cloud Run                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Auth        │  │  Document    │  │   AI Service       │  │
│  │  Service     │  │  Pipeline    │  │  - Clarifier       │  │
│  │  (JWT+RBAC)  │  │  - Parser    │  │  - Tutor           │  │
│  │              │  │  - OCR       │  │  - STT             │  │
│  └──────────────┘  └──────────────┘  └────────────────────┘  │
│                                                              │
│  Libraries: SQLAlchemy 2.0, Pydantic v2, Celery, slowapi     │
│  Parsing: python-docx, PyMuPDF, pdfplumber                   │
└───────┬──────────────────┬───────────────────┬───────────────┘
        │                  │                   │
┌───────┴───────┐  ┌───────┴───────┐  ┌────────┴──────────────┐
│  PostgreSQL   │  │    Redis      │  │   External Services   │
│  16           │  │    7          │  │  - Gemini 2.0 Flash   │
│  (Cloud SQL)  │  │  (Cache +     │  │  - Whisper API        │
│               │  │   Queue +     │  │  - Google Cloud STT   │
│               │  │   Rate Limit) │  │  - Google Cloud Vision│
│               │  │               │  │  - Mathpix API        │
└───────────────┘  └───────────────┘  └───────────────────────┘

File Storage: Google Cloud Storage
CI/CD: GitHub Actions
Monitoring: Sentry + Cloud Monitoring
```

---

## 3. Tech Stack Final

### 3.1 Frontend

| Komponen | Teknologi | Versi Minimum | Justifikasi |
|----------|-----------|---------------|-------------|
| Framework | Next.js (App Router) | 14+ | SSR untuk FCP < 1.5s; route announcer bawaan untuk screen reader; React ecosystem matang |
| Bahasa | TypeScript | 5.x | Type safety, autocomplete, mengurangi runtime error |
| Styling | Tailwind CSS | 3.x | Utility-first, custom a11y tokens (focus ring, contrast), purge unused CSS |
| Math Rendering | MathJax | 4.x | Accessibility leader: built-in speech, Braille, interactive exploration sub-expression |
| A11y Primitives | React Aria (Adobe) | Latest | Modal, focus trap, live region, combobox — WAI-ARIA compliant out-of-box |
| Earcon Engine | Web Audio API | Native | Latency < 15ms, sintetis tanpa file audio, browser-native |
| Voice Input | MediaDevices API | Native | getUserMedia() untuk push-to-talk recording |
| Linting A11y | eslint-plugin-jsx-a11y | Latest | Compile-time accessibility checks |
| Testing | Playwright + axe-core + Jest | Latest | E2E + automated a11y + unit tests |

### 3.2 Backend

| Komponen | Teknologi | Versi Minimum | Justifikasi |
|----------|-----------|---------------|-------------|
| Framework | FastAPI | 0.110+ | Async native, auto OpenAPI docs, Pydantic integration |
| Bahasa | Python | 3.12+ | Ekosistem parsing dokumen terlengkap |
| ORM | SQLAlchemy | 2.0+ | Async support, mature, migration via Alembic |
| Migration | Alembic | Latest | Database version control |
| Validation | Pydantic | 2.x | Request/response schema validation |
| Auth | PyJWT + bcrypt | Latest | JWT token generation + password hashing |
| Rate Limiting | slowapi | Latest | Tiered rate limiting per endpoint per role |
| Task Queue | Celery | 5.x | Async task processing untuk parsing + AI calls |
| Testing | pytest + httpx | Latest | Async test client untuk FastAPI |

### 3.3 Document Parsing Pipeline

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| DOCX Text | python-docx | Ekstraksi heading, paragraf, tabel |
| DOCX Math | Custom XML parser (zipfile + ElementTree) | Ekstraksi OMML → konversi ke LaTeX |
| DOCX Math Fallback | docxlatex | Fallback jika custom parser gagal |
| PDF Text | PyMuPDF (fitz) | Ekstraksi teks dari PDF digital (primary) |
| PDF Layout | pdfplumber | Fallback untuk tabel dan layout kompleks |
| OCR Text | Google Cloud Vision | Fallback untuk PDF scan — teks umum |
| OCR Math | Mathpix API | Khusus notasi matematika → LaTeX output |

### 3.4 AI & Speech Services

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| LLM | Gemini 2.0 Flash | Semantic clarifier (narasi matematika) + Socratic tutor |
| STT Primary | Whisper API (large-v3) | Speech-to-text Bahasa Indonesia (batch/finished) |
| STT Fallback | Google Cloud STT | Streaming real-time fallback |

### 3.5 Data & Infrastructure

| Komponen | Teknologi | Justifikasi |
|----------|-----------|-------------|
| Database | PostgreSQL 16 (Cloud SQL) | Relational model cocok dengan entitas PRD; JSONB untuk parsed content fleksibel |
| Cache & Queue | Redis 7 | Rate limit counter, Celery broker, session cache |
| File Storage | Google Cloud Storage | Menyimpan file upload guru (DOCX, PDF) |
| Frontend Hosting | Vercel | Optimized untuk Next.js, edge network, auto-SSL |
| Backend Hosting | Google Cloud Run | Containerized, auto-scaling, pay-per-use |
| CI/CD | GitHub Actions | Build, test, deploy automation |
| Error Tracking | Sentry | Real-time error monitoring frontend + backend |
| Infra Monitoring | Google Cloud Monitoring | Uptime, latency, resource metrics |

---

## 4. Architecture Decision Records (ADR)

### ADR-001: Next.js 14 sebagai Frontend Framework

**Status:** Accepted  
**Context:** Platform membutuhkan FCP < 1.5s, kompatibilitas screen reader penuh, dan dual-mode rendering visual + semantik.  
**Decision:** Next.js 14+ dengan App Router dan Server Components.  
**Rationale:**
1. SSR native — HTML semantik dikirim dari server, screen reader langsung membaca tanpa menunggu hydration.
2. React Aria tersedia sebagai library primitif accessible yang mature (modal, focus trap, live region) — menyelesaikan FR-12/FR-13/FR-16.
3. Route announcer bawaan — otomatis mengumumkan navigasi halaman ke screen reader.
4. eslint-plugin-jsx-a11y terintegrasi — mencegah pelanggaran accessibility pada development time.

**Alternatives Rejected:**
- Astro — bagus untuk content-static tapi kurang cocok untuk interaksi kompleks (tutor modal, push-to-talk).
- Remix/React Router — progressive enhancement bagus tapi ekosistem accessibility library lebih kecil.
- Plain HTML + vanilla JS — terlalu banyak reinvent the wheel untuk focus management dan ARIA patterns.

---

### ADR-002: Python FastAPI sebagai Backend Framework

**Status:** Accepted  
**Context:** Backend harus melayani parsing dokumen, integrasi AI, dan orkestrasi pipeline.  
**Decision:** Python FastAPI.  
**Rationale:**
1. Ekosistem parsing 100% Python — python-docx, PyMuPDF, pdfplumber semuanya native Python.
2. Gemini SDK Python adalah first-class citizen dari Google.
3. Async native — FastAPI mendukung async/await untuk non-blocking AI API calls.
4. Pydantic v2 untuk validasi request/response schema yang ketat.
5. Auto-generated OpenAPI docs — FastAPI otomatis menghasilkan Swagger UI.

**Alternatives Rejected:**
- Node.js/Express — Mammoth.js tidak support OMML, tidak ada equivalent PyMuPDF/pdfplumber di Node.
- Django — terlalu banyak overhead untuk API-focused service.

---

### ADR-003: MathJax 4 untuk Math Rendering

**Status:** Accepted  
**Context:** Platform membutuhkan render rumus visual + screen reader accessible untuk siswa tunanetra.  
**Decision:** MathJax 4.  
**Rationale:**
1. Built-in accessibility extensions — speech generation, interactive exploration sub-expression, Braille support.
2. Native ARIA + MathML output — screen reader dapat menavigasi struktur matematika.
3. MathJax 4 telah mengurangi bundle size dan meningkatkan render speed dibanding v3.
4. Untuk platform yang menargetkan siswa tunanetra, accessibility harus menang atas performance.

**Trade-off:**
- Bundle size lebih besar dari KaTeX (~150KB vs ~28KB). Mitigasi: lazy-load MathJax hanya pada halaman yang memiliki rumus; gunakan SSR pre-rendering untuk FCP.

**Dual-Layer Strategy:**
- MathJax visual render + custom `aria-label` dari narasi AI yang diverifikasi guru.
- `aria-label` override MathJax default speech karena narasi guru lebih akurat untuk konteks bahasa Indonesia.

---

### ADR-004: Whisper API + Google Cloud STT untuk Speech-to-Text

**Status:** Accepted  
**Context:** Siswa bertanya via push-to-talk dalam Bahasa Indonesia dengan istilah matematika.  
**Decision:** Whisper API large-v3 (primary) + Google Cloud STT (fallback).  
**Rationale:**
1. Whisper large-v3 memiliki WER terbaik untuk Bahasa Indonesia, terutama pada audio noisy.
2. Google Cloud STT unggul pada streaming/real-time sebagai fallback.
3. Dual-provider memberi resiliensi — jika satu down, yang lain masih berjalan.

**Post-processing:** Buat normalization layer untuk istilah matematika: "satu per dua" → ½, "pangkat dua" → ², dll.

**Alternatives Rejected:**
- Vosk Indo (offline) — WER terlalu tinggi; self-hosted menambah infra complexity.

---

### ADR-005: Google Cloud Vision + Mathpix (Menggantikan Baidu OCR)

**Status:** Accepted  
**Context:** OCR diperlukan sebagai fallback untuk PDF scan dan untuk mengenali notasi matematika.  
**Decision:** Google Cloud Vision (teks umum) + Mathpix API (notasi matematika).  
**Rationale:**
1. Baidu OCR memiliki concern: latency server China, dokumentasi Mandarin, data privacy kurang transparent.
2. Google Cloud Vision: server region Asia, compliance GDPR/SOC2, integrasi native dengan GCP.
3. Mathpix: gold standard untuk math OCR — menghasilkan LaTeX langsung dari gambar rumus.

**Cost Estimate:**
- Mathpix: ~$0.004/request
- GCV: ~$1.50/1000 pages
- Acceptable untuk volume pendidikan

---

### ADR-006: SSE untuk Status Update Parsing

**Status:** Accepted  
**Context:** Proses parsing + AI bisa 30-120 detik, guru perlu tahu progress.  
**Decision:** SSE (Server-Sent Events) via endpoint `GET /api/v1/documents/{id}/progress`.  
**Rationale:**
1. Lebih sederhana dari WebSocket untuk komunikasi satu arah (server → client).
2. Otomatis reconnect pada disconnection.
3. Native `EventSource` API di browser — no library needed.
4. Screen reader compatible — progress diupdate ke aria-live region.

**Alternatives Rejected:**
- WebSocket — overkill untuk one-way status update.
- Polling — wasteful dan latency lebih tinggi.

---

### ADR-007: JWT + httpOnly Cookie untuk Authentication

**Status:** Accepted  
**Context:** Frontend (Vercel) dan Backend (Cloud Run) di-deploy terpisah — butuh auth stateless.  
**Decision:** JWT access token (in-memory) + refresh token (httpOnly secure cookie).  
**Rationale:**
1. Stateless — tidak perlu session store di backend.
2. Cross-origin friendly — frontend dan backend beda domain.
3. httpOnly cookie untuk refresh token mencegah XSS theft.
4. Access token di memory — tidak tersimpan di localStorage.

**Token Policy:**
- Access token lifetime: 15 menit
- Refresh token lifetime: 7 hari
- Password hashing: bcrypt (cost factor 12)

**RBAC Roles:**
- `student` — membaca modul, menggunakan tutor
- `teacher` — upload, review, edit, approve, publish
- `admin` — kelola user, lihat system logs

---

## 5. Database Schema

### 5.1 Entity Relationship Diagram

```
users (1) ──────< (N) documents
users (1) ──────< (N) tutor_sessions
documents (1) ──< (N) math_expressions
documents (1) ──── (1) learning_modules
learning_modules (1) ──< (N) tutor_sessions
tutor_sessions (1) ──< (N) tutor_messages
```

### 5.2 Tabel Inti

#### users
| Kolom | Tipe | Constraint |
|-------|------|------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| role | VARCHAR(20) | NOT NULL, CHECK (role IN ('teacher', 'student', 'admin')) |
| full_name | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

#### documents
| Kolom | Tipe | Constraint |
|-------|------|------------|
| id | UUID | PK |
| teacher_id | UUID | FK → users(id), NOT NULL |
| title | VARCHAR(500) | NOT NULL |
| file_type | VARCHAR(10) | NOT NULL, CHECK IN ('docx', 'pdf') |
| original_file_path | TEXT | NOT NULL |
| parsing_status | VARCHAR(20) | DEFAULT 'pending', CHECK IN ('pending', 'processing', 'parsed', 'failed') |
| ocr_used | VARCHAR(20) | DEFAULT 'none', CHECK IN ('none', 'gcv', 'mathpix') |
| raw_structure | JSONB | Nullable — hasil parsing mentah |
| error_code | VARCHAR(20) | Nullable — kode error jika gagal |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

#### math_expressions
| Kolom | Tipe | Constraint |
|-------|------|------------|
| id | UUID | PK |
| document_id | UUID | FK → documents(id), NOT NULL |
| original_notation | TEXT | NOT NULL — notasi asli dari dokumen |
| latex_representation | TEXT | Nullable — hasil konversi ke LaTeX |
| ai_narration | TEXT | Nullable — narasi hasil AI |
| teacher_narration | TEXT | Nullable — narasi final setelah edit guru |
| status | VARCHAR(20) | DEFAULT 'pending', CHECK IN ('pending', 'ai_generated', 'reviewed', 'approved') |
| position_order | INT | NOT NULL — urutan dalam dokumen |
| created_at | TIMESTAMPTZ | DEFAULT now() |

#### learning_modules
| Kolom | Tipe | Constraint |
|-------|------|------------|
| id | UUID | PK |
| document_id | UUID | FK → documents(id), UNIQUE, NOT NULL |
| html_content | TEXT | NOT NULL — HTML semantik final |
| is_published | BOOLEAN | DEFAULT false |
| published_at | TIMESTAMPTZ | Nullable |
| approved_by | UUID | FK → users(id), Nullable |

#### tutor_sessions
| Kolom | Tipe | Constraint |
|-------|------|------------|
| id | UUID | PK |
| student_id | UUID | FK → users(id), NOT NULL |
| module_id | UUID | FK → learning_modules(id), NOT NULL |
| context_element_id | VARCHAR(100) | Nullable — ID elemen HTML yang aktif saat tutor dibuka |
| started_at | TIMESTAMPTZ | DEFAULT now() |
| ended_at | TIMESTAMPTZ | Nullable |

#### tutor_messages
| Kolom | Tipe | Constraint |
|-------|------|------------|
| id | UUID | PK |
| session_id | UUID | FK → tutor_sessions(id), NOT NULL |
| role | VARCHAR(10) | NOT NULL, CHECK IN ('student', 'tutor') |
| content | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### 5.3 Index Strategy

```sql
CREATE INDEX idx_documents_teacher ON documents(teacher_id);
CREATE INDEX idx_documents_status ON documents(parsing_status);
CREATE INDEX idx_math_expr_document ON math_expressions(document_id);
CREATE INDEX idx_math_expr_status ON math_expressions(status);
CREATE INDEX idx_modules_published ON learning_modules(is_published) WHERE is_published = true;
CREATE INDEX idx_tutor_sessions_student ON tutor_sessions(student_id);
CREATE INDEX idx_tutor_messages_session ON tutor_messages(session_id);
```

---

## 6. API Specification

### 6.1 Base URL
```
Production: https://api.inklusifmath.id/api/v1
Development: http://localhost:8000/api/v1
```

### 6.2 Authentication Endpoints

#### POST /auth/register
**Deskripsi:** Registrasi user baru.  
**Auth:** None (public)  
**Request Body:**
```json
{
  "email": "guru@sekolah.id",
  "password": "SecureP@ss123",
  "full_name": "Budi Hartono",
  "role": "teacher"
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "email": "guru@sekolah.id",
  "role": "teacher",
  "full_name": "Budi Hartono"
}
```
**Error:** 409 (email exists), 422 (validation error)

---

#### POST /auth/login
**Deskripsi:** Login dan dapatkan access token.  
**Auth:** None  
**Request Body:**
```json
{
  "email": "guru@sekolah.id",
  "password": "SecureP@ss123"
}
```
**Response 200:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```
**Side Effect:** Set httpOnly cookie `refresh_token`  
**Error:** 401 (invalid credentials), 429 (rate limited)

---

#### POST /auth/refresh
**Deskripsi:** Refresh access token menggunakan refresh token di cookie.  
**Auth:** httpOnly cookie (refresh_token)  
**Response 200:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```
**Error:** 401 (invalid/expired refresh token)

---

### 6.3 Document Endpoints

#### POST /documents/upload
**Deskripsi:** Upload dokumen guru untuk diproses.  
**Auth:** Bearer JWT (role: teacher, admin)  
**Request:** multipart/form-data  
**Fields:** `file` (required), `title` (required, string)  
**Response 202:**
```json
{
  "document_id": "uuid",
  "title": "Pecahan Kelas 5",
  "status": "processing",
  "message": "Dokumen sedang diproses"
}
```
**Error:** 413 (DOC_001: file > 20MB), 415 (DOC_002: format invalid), 422 (DOC_003: file corrupt)

---

#### GET /documents/{id}/status
**Deskripsi:** Cek status proses dokumen.  
**Auth:** Bearer JWT (role: teacher, admin)  
**Response 200:**
```json
{
  "document_id": "uuid",
  "status": "parsed",
  "ocr_used": "none",
  "math_expressions_count": 12,
  "created_at": "2026-09-16T08:00:00Z"
}
```

---

#### GET /documents/{id}/progress (SSE)
**Deskripsi:** Stream progress parsing secara real-time.  
**Auth:** Bearer JWT (role: teacher, admin)  
**Response:** text/event-stream
```
data: {"step": "extracting_text", "progress": 30, "message": "Mengekstrak teks..."}

data: {"step": "detecting_math", "progress": 60, "message": "Mendeteksi rumus matematika..."}

data: {"step": "generating_narration", "progress": 80, "message": "Menghasilkan narasi AI..."}

data: {"step": "complete", "progress": 100, "message": "Selesai"}
```

---

#### GET /documents/{id}/narrations
**Deskripsi:** Ambil semua narasi AI untuk review guru.  
**Auth:** Bearer JWT (role: teacher, admin)  
**Response 200:**
```json
{
  "document_id": "uuid",
  "title": "Pecahan Kelas 5",
  "expressions": [
    {
      "id": "uuid",
      "original_notation": "2/3 + 1/4",
      "latex": "\\frac{2}{3} + \\frac{1}{4}",
      "ai_narration": "pecahan dua per tiga ditambah pecahan satu per empat",
      "teacher_narration": null,
      "status": "ai_generated",
      "position_order": 1
    }
  ]
}
```

---

### 6.4 Review Endpoints

#### PATCH /narrations/{id}
**Deskripsi:** Guru mengedit narasi AI.  
**Auth:** Bearer JWT (role: teacher, admin)  
**Request Body:**
```json
{
  "teacher_narration": "pecahan dengan pembilang dua dan penyebut tiga, ditambah pecahan dengan pembilang satu dan penyebut empat"
}
```
**Response 200:**
```json
{
  "id": "uuid",
  "status": "reviewed",
  "teacher_narration": "..."
}
```

---

#### POST /documents/{id}/approve
**Deskripsi:** Guru menyetujui semua narasi dan mempublikasikan modul.  
**Auth:** Bearer JWT (role: teacher, admin)  
**Pre-condition:** Semua math_expressions harus berstatus 'reviewed' atau 'approved'  
**Response 200:**
```json
{
  "module_id": "uuid",
  "document_id": "uuid",
  "is_published": true,
  "published_at": "2026-09-16T10:00:00Z"
}
```
**Error:** 409 (ada expression yang belum di-review)

---

### 6.5 Module Endpoints

#### GET /modules
**Deskripsi:** Daftar modul yang sudah dipublikasikan.  
**Auth:** Bearer JWT (role: student, teacher, admin)  
**Response 200:**
```json
{
  "modules": [
    {
      "id": "uuid",
      "title": "Pecahan Kelas 5",
      "published_at": "2026-09-16T10:00:00Z"
    }
  ]
}
```

---

#### GET /modules/{id}
**Deskripsi:** Ambil konten modul lengkap.  
**Auth:** Bearer JWT (role: student, teacher, admin)  
**Response 200:**
```json
{
  "id": "uuid",
  "title": "Pecahan Kelas 5",
  "html_content": "<article>...</article>",
  "math_expressions": [
    {
      "id": "uuid",
      "latex": "\\frac{2}{3}",
      "narration": "pecahan dengan pembilang dua dan penyebut tiga",
      "position_order": 1
    }
  ]
}
```

---

### 6.6 Tutor Endpoints

#### POST /tutor/ask
**Deskripsi:** Kirim pertanyaan siswa ke tutor AI.  
**Auth:** Bearer JWT (role: student, teacher)  
**Rate Limit:** 30/jam (student), 60/jam (teacher)  
**Request Body:**
```json
{
  "module_id": "uuid",
  "context_element_id": "section-pecahan-3",
  "transcript_text": "kenapa dua per tiga ditambah satu per empat hasilnya bukan tiga per tujuh?"
}
```
**Response 200:**
```json
{
  "session_id": "uuid",
  "answer_text": "Pertanyaan bagus! Coba ingat, apakah kamu bisa langsung menjumlahkan dua pecahan yang penyebutnya berbeda? Apa yang harus disamakan terlebih dahulu?",
  "follow_up_hint": "Pikirkan tentang KPK dari kedua penyebut."
}
```
**Error:** 429 (rate limited), 503 (AI_003: tutor unavailable)

---

## 7. Error Handling Taxonomy

| Kode | Domain | Error | HTTP Status | Perilaku Sistem |
|------|--------|-------|-------------|-----------------|
| DOC_001 | Upload | File terlalu besar (> 20MB) | 413 | Reject upload |
| DOC_002 | Upload | Format tidak didukung | 415 | Reject upload |
| DOC_003 | Upload | File corrupt / tidak bisa dibaca | 422 | Reject upload |
| PARSE_001 | Parsing | Gagal ekstraksi teks PDF | — | Coba OCR fallback otomatis |
| PARSE_002 | Parsing | OCR fallback juga gagal | 422 | Minta upload ulang |
| PARSE_003 | Parsing | Tidak ditemukan notasi matematika | 200 | Lanjut tanpa narasi AI |
| AI_001 | Clarifier | Gemini API timeout (> 30s) | — | Retry 2x, lalu queue |
| AI_002 | Clarifier | Gemini API error/down | — | Queue + notifikasi |
| AI_003 | Tutor | Gemini API timeout | 503 | Pesan fallback |
| STT_001 | Tutor | Mikrofon tidak diizinkan | — | Client-side: minta izin ulang |
| STT_002 | Tutor | Whisper gagal transkripsi | 422 | Minta ulang |
| STT_003 | Tutor | Transkripsi kosong | 422 | Minta ulang |
| AUTH_001 | Auth | Token expired | 401 | Client: refresh otomatis |
| AUTH_002 | Auth | Refresh token expired | 401 | Client: redirect login |

**Semua pesan error harus accessible:** ditampilkan di `aria-live="assertive"` region agar langsung diumumkan screen reader.

---

## 8. Rate Limiting Strategy

| Endpoint | Role | Limit | Window |
|----------|------|-------|--------|
| POST /tutor/ask | student | 30 | per jam |
| POST /tutor/ask | teacher | 60 | per jam |
| POST /documents/upload | teacher | 10 file | per hari |
| POST /auth/login | semua | 5 attempt | per 15 menit |
| Semua endpoint | semua | 200 request | per menit |

**Implementasi:** slowapi (FastAPI) + Redis counter  
**Response:** HTTP 429 + `Retry-After` header + pesan accessible

---

## 9. Authentication & Authorization

### 9.1 Mekanisme
- Access Token: JWT, lifetime 15 menit, disimpan di memory client
- Refresh Token: lifetime 7 hari, disimpan di httpOnly secure cookie
- Password: bcrypt, cost factor 12

### 9.2 RBAC Matrix

| Aksi | student | teacher | admin |
|------|---------|---------|-------|
| Membaca modul | ✅ | ✅ | ✅ |
| Menggunakan tutor | ✅ | ✅ | ✅ |
| Upload dokumen | ❌ | ✅ | ✅ |
| Review/edit narasi | ❌ | ✅ | ✅ |
| Approve/publish | ❌ | ✅ | ✅ |
| Menarik kembali modul | ❌ | ✅ | ✅ |
| Mengelola user | ❌ | ❌ | ✅ |
| Melihat system logs | ❌ | ❌ | ✅ |

---

## 10. Metrik Target (Revisi)

| Metrik | Target |
|--------|--------|
| Focus Disorientation Rate | < 2% |
| Audio Collision Incidents | 0 |
| Math Pronunciation Accuracy | ≥ 98% (dengan human-in-the-loop) |
| Time-to-Inquire | < 8 detik |
| Earcon latency | < 15 ms |
| ASR WER (Bahasa Indonesia, matematika) | < 12% |
| First Contentful Paint modul | < 1.5 detik |
| Accessibility Audit (Axe/Lighthouse) | ≥ 95/100, 0 critical issues |

---

## 11. Document Parsing Pipeline Detail

### 11.1 DOCX Pipeline
```
DOCX file
  │
  ├─ python-docx → Extract headings, paragraphs, tables
  │
  ├─ zipfile + ElementTree → Extract <m:oMath> XML nodes
  │     │
  │     ├─ Custom OMML → LaTeX converter
  │     │
  │     └─ Fallback: docxlatex library
  │
  └─ Merge: structured content + LaTeX expressions
       │
       └─ Send to AI Clarifier (Gemini) → narasi verbal
```

### 11.2 PDF Pipeline
```
PDF file
  │
  ├─ PyMuPDF (fitz.open) → Extract text
  │     │
  │     ├─ Text found? → Parse structure (headings, paragraphs)
  │     │                  │
  │     │                  ├─ Detect inline math patterns → LaTeX
  │     │                  │
  │     │                  └─ Detect math images → Mathpix API → LaTeX
  │     │
  │     └─ Text empty? → PDF scan detected
  │                       │
  │                       ├─ Google Cloud Vision → Extract text
  │                       │
  │                       ├─ Mathpix API → Extract math → LaTeX
  │                       │
  │                       └─ Merge results → Parse structure
  │
  └─ Send to AI Clarifier (Gemini) → narasi verbal
```

---

## 12. Roadmap Implementasi

### Fase 1 — Foundation (4-6 minggu)
- Project setup: Next.js + FastAPI + PostgreSQL + Redis
- Database schema + Alembic migrations
- JWT auth system + RBAC middleware
- Accessible page template (WCAG 2.2 AA baseline)
- DOCX parser (python-docx + OMML extraction)
- CI/CD pipeline + Axe Core automated testing
- Basic deployment (Vercel + Cloud Run)

### Fase 2 — Core Pipeline (4-6 minggu)
- PDF text extraction (PyMuPDF)
- OCR fallback pipeline (Google Cloud Vision + Mathpix)
- AI Semantic Clarifier integration (Gemini)
- Portal review guru (two-column layout)
- Dual-layer math rendering (MathJax 4 + aria-label)
- Module publication flow + SSE progress

### Fase 3 — Tutor & Interaction (4-6 minggu)
- Earcon engine (Web Audio API)
- Accessible modal tutor (React Aria)
- Push-to-talk (MediaDevices API)
- STT integration (Whisper API + Google Cloud STT fallback)
- AI Tutor integration (Gemini, Socratic prompt)
- Focus management system (save/trap/restore)
- aria-live region output
- Rate limiting (slowapi + Redis)

### Fase 4 — QA & Field Testing (4-6 minggu)
- Screen reader testing matrix (NVDA, JAWS, VoiceOver, TalkBack)
- Microphone calibration testing
- Load testing & rate limiting validation
- Security audit (OWASP ZAP)
- Field testing dengan siswa tunanetra
- Accessibility Conformance Report
- Documentation & deployment finalization
