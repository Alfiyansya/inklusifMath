# InklusifMath — AI Context Document

> **Last Updated:** 2026-09-16  
> **Branch:** `main`  
> **Latest Commit:** `8b235e5` — fix: match exact Figma colors, logo, and fonts

---

## 1. Apa Itu InklusifMath?

Platform e-learning matematika yang **aksesibel untuk siswa tunanetra** di Indonesia. Guru mengunggah modul (.docx/.pdf), sistem AI mengekstraksi rumus matematika, membangkitkan narasi verbal Bahasa Indonesia, lalu menerbitkan modul yang bisa dibaca screen reader. Ada juga Tutor AI Sokrates yang bisa ditanya siswa via push-to-talk.

**Target compliance:** WCAG 2.2 AA, WAI-ARIA 1.2

---

## 2. Tech Stack (Final, Approved)

| Layer | Teknologi | Versi |
|-------|-----------|-------|
| **Frontend** | Next.js (App Router) + TypeScript | 16.3.5 |
| **Styling** | Tailwind CSS v4 + CSS custom properties | 4.x |
| **A11y UI** | React Aria | latest |
| **Math Rendering** | MathJax 4 | — |
| **Backend** | FastAPI + SQLAlchemy 2.0 (async) | 0.115+ |
| **Database** | PostgreSQL 16 | 16 |
| **Cache** | Redis 7 | 7 |
| **Auth** | JWT (access 15min) + httpOnly cookie (refresh 7d) | — |
| **Password** | bcrypt (cost factor 12) | — |
| **OCR** | Google Cloud Vision + Mathpix (planned) | — |
| **STT** | Whisper API + Google Cloud STT (planned) | — |
| **Python** | 3.14 | 3.14.7 |
| **Package Manager** | pip (venv) / npm | — |
| **Migration** | Alembic (async) | — |
| **CI** | GitHub Actions | — |

---

## 3. Project Structure

```
inklusifMath/
├── docs/                          # Project documentation
│   ├── prd_ai_friendly_inklusifmath.md   # Product Requirements (revised)
│   ├── srs_inklusifmath.md               # Software Requirements (revised)
│   ├── tdd_inklusifmath.md               # Technical Design Document
│   └── leksikon_matematika_baku.md       # Math narration lexicon (50+ entries)
│
├── backend/                       # FastAPI backend
│   ├── app/
│   │   ├── main.py                # FastAPI app entry (CORS, rate limiter, router)
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic Settings (env vars)
│   │   │   ├── database.py        # SQLAlchemy 2.0 async engine + session
│   │   │   ├── security.py        # JWT create/decode + bcrypt
│   │   │   ├── dependencies.py    # get_current_user + require_role factory
│   │   │   └── rate_limiter.py    # slowapi Limiter
│   │   ├── models/
│   │   │   ├── __init__.py        # ⚠ IMPORTANT: imports ALL models for relationship resolution
│   │   │   ├── user.py            # User (id, email, password_hash, role, full_name)
│   │   │   ├── document.py        # Document, MathExpression, LearningModule
│   │   │   └── tutor.py           # TutorSession, TutorMessage
│   │   ├── schemas/
│   │   │   ├── auth.py            # RegisterRequest, LoginRequest, TokenResponse, UserResponse
│   │   │   ├── document.py        # Document/narration schemas
│   │   │   ├── module.py          # Module list/detail schemas
│   │   │   └── tutor.py           # Tutor ask/response schemas
│   │   ├── api/v1/
│   │   │   ├── router.py          # Aggregates all endpoint routers
│   │   │   └── endpoints/
│   │   │       ├── auth.py        # ✅ IMPLEMENTED: register, login, refresh, logout
│   │   │       ├── documents.py   # ❌ STUB: upload, list, get, narrations
│   │   │       ├── modules.py     # ❌ STUB: list, get, publish
│   │   │       └── tutor.py       # ❌ STUB: ask (with rate limiting)
│   │   └── services/
│   │       ├── auth.py            # ✅ AuthService (register, authenticate, tokens)
│   │       ├── ai/               # ❌ EMPTY: future AI services
│   │       └── parsing/          # ❌ EMPTY: future DOCX/PDF parser
│   ├── alembic/                   # Database migrations
│   │   ├── env.py                 # Configured for async PostgreSQL
│   │   └── versions/
│   │       ├── 850d2a6c7593_initial_schema.py
│   │       └── bf496f6764d6_fix_datetime_to_timestamptz.py
│   ├── tests/
│   │   ├── conftest.py            # Session-scoped AsyncClient + DB cleanup
│   │   ├── test_health.py         # 1 test (health endpoint)
│   │   └── test_auth.py           # 11 tests (register, login, protected, logout)
│   ├── requirements.txt           # Python dependencies (min version pins)
│   ├── pyproject.toml             # pytest-asyncio config (session loop scope)
│   └── .env                       # Dev environment vars
│
├── frontend/                      # Next.js 16 frontend
│   ├── src/app/
│   │   ├── layout.tsx             # Root layout (Inter + Poppins fonts, lang="id")
│   │   ├── page.tsx               # Redirect / → /dashboard
│   │   ├── globals.css            # Design tokens as CSS custom properties
│   │   ├── dashboard/
│   │   │   ├── layout.tsx         # Dashboard layout (wraps with Header)
│   │   │   └── page.tsx           # ✅ Teacher home (hero, stats, modules, shortcuts)
│   │   └── upload/
│   │       ├── page.tsx           # ✅ Upload module page (drag-and-drop)
│   │       └── [id]/review/
│   │           └── page.tsx       # ✅ Narration review (LaTeX + verbal editor)
│   ├── src/components/
│   │   ├── layout/
│   │   │   └── Header.tsx         # Logo, user info, logout button
│   │   ├── ui/
│   │   │   ├── StatCard.tsx       # Stat number + label
│   │   │   ├── ModuleCard.tsx     # Module card with tags + status
│   │   │   ├── FeatureList.tsx    # Accessibility features box
│   │   │   ├── KeyboardShortcuts.tsx # Keyboard shortcuts legend
│   │   │   ├── SkipLink.tsx       # WCAG 2.4.1 bypass block
│   │   │   └── LiveRegion.tsx     # aria-live announcer
│   │   └── teacher/
│   │       ├── UploadZone.tsx     # Drag-and-drop file upload + progress
│   │       └── NarrationCard.tsx  # Two-column LaTeX + narration editor
│   ├── src/hooks/
│   │   ├── useFocusRestore.ts     # Focus save/restore for modals
│   │   └── useGlobalShortcut.ts   # Global keyboard shortcut handler
│   ├── src/lib/
│   │   ├── api/client.ts          # API client with JWT auto-refresh
│   │   └── audio/earcon.ts        # Web Audio earcon engine (5 sounds)
│   ├── src/types/index.ts         # Full TypeScript type definitions
│   └── public/logo.png            # App logo from Figma
│
├── docker-compose.yml             # PostgreSQL 16 + Redis 7
├── .github/workflows/ci.yml      # Backend test + frontend build + Lighthouse a11y
├── .gitignore                     # Comprehensive monorepo gitignore
└── README.md                      # Quick start guide
```

---

## 4. Database Schema (6 Tables)

```
users
  id            UUID PK
  email         VARCHAR(255) UNIQUE
  password_hash VARCHAR(255)
  role          VARCHAR(20)  -- 'teacher' | 'student' | 'admin'
  full_name     VARCHAR(255)
  created_at    TIMESTAMPTZ
  updated_at    TIMESTAMPTZ

documents
  id                UUID PK
  teacher_id        UUID FK → users.id
  title             VARCHAR(500)
  file_type         VARCHAR(10)
  original_file_path TEXT
  parsing_status    VARCHAR(20) -- 'pending' | 'processing' | 'completed' | 'failed'
  ocr_used          VARCHAR(20)
  raw_structure     JSONB
  error_code        VARCHAR(20)
  created_at/updated_at TIMESTAMPTZ

math_expressions
  id                  UUID PK
  document_id         UUID FK → documents.id
  original_notation   TEXT
  latex_representation TEXT
  ai_narration        TEXT
  teacher_narration   TEXT
  status              VARCHAR(20)
  position_order      INTEGER
  created_at          TIMESTAMPTZ

learning_modules
  id            UUID PK
  document_id   UUID FK → documents.id (UNIQUE)
  html_content  TEXT
  is_published  BOOLEAN
  published_at  TIMESTAMPTZ
  approved_by   UUID FK → users.id

tutor_sessions
  id                  UUID PK
  student_id          UUID FK → users.id
  module_id           UUID FK → learning_modules.id
  context_element_id  VARCHAR(100)
  started_at          TIMESTAMPTZ
  ended_at            TIMESTAMPTZ

tutor_messages
  id          UUID PK
  session_id  UUID FK → tutor_sessions.id
  role        VARCHAR(10) -- 'user' | 'assistant'
  content     TEXT
  created_at  TIMESTAMPTZ
```

Migrations sudah applied. Semua datetime columns menggunakan `TIMESTAMPTZ`.

---

## 5. API Endpoints

| Method | Endpoint | Status | Auth |
|--------|----------|--------|------|
| GET | `/health` | ✅ Implemented | No |
| POST | `/api/v1/auth/register` | ✅ Implemented | No |
| POST | `/api/v1/auth/login` | ✅ Implemented | No |
| POST | `/api/v1/auth/refresh` | ✅ Implemented | Cookie |
| POST | `/api/v1/auth/logout` | ✅ Implemented | No |
| POST | `/api/v1/documents/upload` | ❌ Stub | Teacher |
| GET | `/api/v1/documents` | ❌ Stub | Teacher |
| GET | `/api/v1/documents/{id}` | ❌ Stub | Teacher |
| PUT | `/api/v1/documents/{id}/narrations` | ❌ Stub | Teacher |
| GET | `/api/v1/modules` | ❌ Stub (returns []) | Any |
| GET | `/api/v1/modules/{id}` | ❌ Stub | Any |
| POST | `/api/v1/modules/{id}/publish` | ❌ Stub | Teacher |
| POST | `/api/v1/tutor/ask` | ❌ Stub | Student |

---

## 6. Design System (from Figma)

```css
--color-primary:        #6495ED   /* Cornflower blue */
--color-primary-hover:  #5280D8
--color-bg-page:        #F0F5FF   /* Light blue page bg */
--color-bg-card:        #FFFFFF
--color-border-card:    #C8DCFA   /* Light blue borders */
--color-text-primary:   #1F2A44   /* Dark navy */
--color-text-secondary: #5A6A8A   /* Muted blue-gray */
--color-text-muted:     #8A9ABB
--color-success:        #10B981   /* Green (✓ Terbit) */
--color-warning:        #F59E0B   /* Orange (⚠ Perlu Perhatian) */
--color-tag-bg:         #EAF3FF
--color-tag-text:       #6495ED
--color-avatar-bg:      #EAF3FF
```

**Fonts:** Inter (body), Poppins ExtraBold (logo title only)

**Figma source:** https://www.figma.com/design/lxROcWm9tTqLRDyy6Y6bhd/WEB-DEV-COMPE?node-id=67-30&m=dev

> **⚠ Tailwind v4 Note:** `@theme inline` crashes Turbopack in Next.js 16. All components use inline `style={{ color: "var(--color-primary)" }}` instead of Tailwind custom color classes. CSS custom properties defined in `:root` in `globals.css`.

---

## 7. Testing

```bash
# Backend (requires Docker PostgreSQL running)
cd backend && .venv/bin/python -m pytest tests/ -v
# Result: 12 passed (1 health + 11 auth)

# Frontend
cd frontend && npx next build
# Result: all routes compiled successfully
```

**pytest-asyncio config:** `asyncio_default_test_loop_scope = "session"` in `pyproject.toml` — required to prevent asyncpg "Event loop is closed" errors.

**Test DB isolation:** `conftest.py` cleans all tables before session and disposes engine after.

---

## 8. Docker Services

```bash
docker compose up -d   # Start PostgreSQL + Redis
```

| Service | Port | Container |
|---------|------|-----------|
| PostgreSQL 16 | 5432 | inklusifmath-db |
| Redis 7 | 6379 | inklusifmath-redis |

**DB credentials (.env):** `DATABASE_URL=postgresql+asyncpg://inklusifmath:inklusifmath_dev@localhost:5432/inklusifmath_db`

---

## 9. What's NOT Implemented Yet (Roadmap)

### Backend — Priority Order:
1. **DOCX/PDF Parser** — `services/parsing/` — Extract text + math from uploaded documents
2. **AI Narration** — `services/ai/` — Generate verbal narration for math expressions using LLM
3. **Document endpoints** — Upload, parse, list, get narrations
4. **Module publish flow** — Teacher approves narrations → publish accessible HTML module
5. **Tutor Sokrates** — AI tutor via push-to-talk (Whisper STT → LLM → TTS)
6. **OCR pipeline** — Google Cloud Vision + Mathpix for PDF scans

### Frontend — Not Yet Connected:
- All pages currently use **static mock data** (not connected to backend API)
- Auth flow UI (login/register pages) — **not built yet**
- `src/lib/api/client.ts` exists but not wired to any page
- MathJax rendering not integrated into NarrationCard yet
- Tutor modal (Alt+T) not built yet

### Infrastructure:
- No test database isolation (tests write to dev DB)
- No production deployment config
- No file storage (S3/GCS) for uploaded documents
- Rate limiting configured but not fine-tuned

---

## 10. Known Quirks & Gotchas

1. **Turbopack + `@theme inline`** — CRASHES. Use `:root` CSS variables + inline styles instead.
2. **`models/__init__.py`** — MUST import all models. SQLAlchemy relationship string references fail otherwise.
3. **`asyncio_default_test_loop_scope = "session"`** — Required in `pyproject.toml`. Without it, asyncpg connections break between tests.
4. **`DateTime(timezone=True)`** — All model datetime columns must use this. asyncpg rejects offset-naive datetimes into TIMESTAMPTZ columns.
5. **Frontend build needs network** — Google Fonts (Inter, Poppins) are fetched during build. Use `BypassSandbox=true` for `npm run build`.
6. **Python 3.14** — `asyncio.iscoroutinefunction` deprecated warning from slowapi; harmless.

---

## 11. Git History

```
8b235e5  fix: match exact Figma colors, logo, and fonts
0a0dff3  feat: redirect root / to /dashboard
42d85f5  feat: implement UI/UX from Figma design
b910f2a  feat: implement auth endpoints (register, login, refresh, logout)
788f4bb  feat: initial project setup — Next.js 16 + FastAPI + PostgreSQL + Redis
```
