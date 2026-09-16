# InklusifMath Platform

Platform e-learning matematika aksesibel untuk siswa tunanetra dan low vision di Indonesia.

## Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Frontend | Next.js 14+ (App Router, SSR), TypeScript, Tailwind CSS, MathJax 4, React Aria |
| Backend | Python FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7, Celery |
| AI | Gemini 2.0 Flash, Whisper API |
| OCR | Google Cloud Vision, Mathpix |

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker & Docker Compose (untuk PostgreSQL dan Redis)

## Quick Start

### 1. Start database services

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with your keys
alembic upgrade head
uvicorn app.main:app --reload
```

Backend berjalan di `http://localhost:8000`
Swagger docs di `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Frontend berjalan di `http://localhost:3000`

## Project Structure

```
inklusifMath/
├── docs/                    # PRD, SRS, TDD, Leksikon
├── frontend/                # Next.js application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities, API client
│   │   └── types/           # TypeScript types
│   └── ...
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, auth, DB
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── alembic/             # DB migrations
│   └── tests/
├── docker-compose.yml       # PostgreSQL + Redis
└── README.md
```

## Accessibility

Platform ini dirancang dengan prinsip **Web Standards First** dan **Zero Audio Collision** untuk memastikan kompatibilitas penuh dengan screen reader native (NVDA, JAWS, VoiceOver, TalkBack).

Target: **WCAG 2.2 Level AA** compliance.

## License

Private — All rights reserved.
