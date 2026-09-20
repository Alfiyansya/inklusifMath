# InklusifMath Platform 📐♿

[![Next.js](https://img.shields.io/badge/Next.js-16.3.5-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis)](https://redis.io/)
[![Google Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-AI-4285F4?style=flat-square&logo=google)](https://ai.google.dev/)
[![WCAG Compliance](https://img.shields.io/badge/WCAG-2.2_AA_Compliant-success?style=flat-square)](https://www.w3.org/WAI/standards-guidelines/wcag/)
[![License](https://img.shields.io/badge/License-Private-lightgrey?style=flat-square)](#lisensi)

> **Platform E-Learning Matematika Aksesibel Berbasis AI untuk Siswa Tunanetra dan *Low Vision* di Indonesia.**

---

## 📑 Daftar Isi

- [Tentang InklusifMath](#-tentang-inklusifmath)
- [Fitur Utama](#-fitur-utama)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Tech Stack](#-tech-stack)
- [Struktur Repositori](#-struktur-repositori)
- [Prasyarat Sistem](#-prasyarat-sistem)
- [Panduan Instalasi Lokal (Quick Start)](#-panduan-instalasi-lokal-quick-start)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Menjalankan Database & Cache (Docker)](#2-menjalankan-database--cache-docker)
  - [3. Setup Backend (FastAPI)](#3-setup-backend-fastapi)
  - [4. Setup Background Worker (Celery)](#4-setup-background-worker-celery-opsional)
  - [5. Setup Frontend (Next.js)](#5-setup-frontend-nextjs)
- [Konfigurasi Environment Variables](#-konfigurasi-environment-variables)
  - [Backend (.env)](#backend-env)
  - [Frontend (.env.local)](#frontend-envlocal)
- [Pengujian (Testing & QA)](#-pengujian-testing--qa)
- [Standar Aksesibilitas & Pintasan Keyboard](#-standar-aksesibilitas--pintasan-keyboard)
- [Deployment Produksi](#-deployment-produksi)
- [Dokumentasi Terkait](#-dokumentasi-terkait)
- [Lisensi](#-lisensi)

---

## 🎯 Tentang InklusifMath

Pembelajaran matematika bagi siswa penyandang disabilitas netra (*blind* dan *low vision*) di Indonesia menghadapi kendala struktural:
1. Materi ajar berformat digital (.docx / .pdf) sering kali memuat ekspresi dan rumus matematika visual yang **tidak dapat dibaca secara bermakna oleh *screen reader* standar** (NVDA, JAWS, VoiceOver, TalkBack).
2. Keterbatasan pendampingan belajar interaktif yang memahami konteks notasi matematika verbal dalam Bahasa Indonesia baku.

**InklusifMath** hadir untuk menjembatani kesenjangan tersebut melalui pendekatan:
- **Web Standards First**: Menggunakan semantik murni HTML5 dan WAI-ARIA 1.2 tanpa bergantung pada modul audio pihak ketiga yang mengganggu pembaca layar bawaan.
- **Zero Audio Collision**: Menjamin suara sintesis aplikasi tidak bertabrakan dengan *screen reader* pengguna.
- **Human-in-the-Loop Verification**: Memberikan hak kendali penuh bagi guru untuk meninjau, mengedit, dan menyetujui narasi verbal yang dihasilkan AI sebelum materi dipublikasikan kepada siswa.

---

## ✨ Fitur Utama

### 1. 📄 Ekstraksi Dokumen Matematis Cerdas (.docx & .pdf)
- **Parser Otomatis**: Mendeteksi struktur bab, subbab, paragraf, tabel, serta memisahkan teks umum dari ekspresi matematika.
- **Konversi OMML ke LaTeX**: Menerjemahkan notasi Office Math Markup Language (.docx) ke representasi LaTeX standar (mencakup 14 konstruksi matematis utama).
- **Dual-Engine OCR Pipeline**: Untuk dokumen pindaian (*scanned PDF* atau gambar), sistem mengombinasikan **Google Cloud Vision (GCV)** untuk deteksi layout teks dan **pix2tex (LaTeX-OCR)** / **Mathpix** untuk pengenalan formula matematika berpresisi tinggi.
- **Real-Time Progress**: Pemantauan progres ekstraksi dokumen secara *real-time* menggunakan **Server-Sent Events (SSE)**.

### 2. 🗣️ Pembangkitan Narasi Verbal Bahasa Indonesia Baku
- Ditenagai oleh **Google Gemini 2.0 Flash** yang dipandu oleh **50+ kaidah Leksikon Baku Matematika Indonesia** (pecahan bertingkat, eksponen, matriks, limit, integral, trigonometri, logika proposisi).
- Menghasilkan narasi fonetis yang deskriptif dan ramah pembaca layar (misal: $\frac{a+b}{c}$ dibaca *"pecahan dengan pembilang a ditambah b dan penyebut c"*).

### 3. 🔄 Math Term Normalization Layer
- Lapisan normalisasi lisan pada frontend dan backend yang mengubah ucapan atau frasa lisan sehari-hari murid menjadi notasi simbolis matematis baku:
  - *"setengah"* $\rightarrow$ `1/2`
  - *"x kuadrat ditambah dua x sama dengan nol"* $\rightarrow$ `x² + 2x = 0`
  - *"akar dari enam belas"* $\rightarrow$ `√16`

### 4. 🤖 Socratic AI Math Tutor
- Asisten belajar cerdas yang membimbing siswa memahami konsep secara mandiri melalui metode dialog **Sokrates** (memberikan petunjuk bertahap tanpa membocorkan jawaban final).
- Input suara interaktif (*Push-to-Talk*) berbasis **Web Speech API** dengan cadangan transkripsi backend berbasis **faster-whisper**.
- Indikasi status audio (*Earcon*) instan (<15ms) via **Web Audio API** sehingga siswa mengetahui status rekaman tanpa menunggu *screen reader*.

### 5. 👥 Portal Guru & Alur Persetujuan (Review Workflow)
- Tampilan perbandingan dua kolom (*Side-by-side Review*): notasi visual LaTeX bersanding dengan narasi audio verbal yang dapat langsung diedit atau diperbarui secara massal (*bulk update*).
- Status siklus hidup dokumen transparan: `pending` $\rightarrow$ `processing` $\rightarrow$ `parsed` $\rightarrow$ `approved` $\rightarrow$ `published`.

### 6. 🔐 Role-Based Access Control (RBAC)
- Otentikasi aman berbasis **Firebase Authentication** dengan sinkronisasi profil pengguna ke **Cloud Firestore** dan validasi otoritas di backend melalui **Firebase Admin SDK**.
- Pembagian peran terisolasi: **Teacher** (unggah, edit narasi, kelola modul), **Student** (baca modul, interaksi AI tutor), dan **Admin**.

---

## 🏛️ Arsitektur Sistem

```mermaid
flowchart TD
    subgraph Pengguna
        G[Guru Matematika]
        S[Siswa Disabilitas Netra]
    end

    subgraph Frontend ["Frontend (Next.js 16 + React Aria)"]
        UI_G[Portal Guru: Upload & Review]
        UI_S[Portal Siswa: Module Reader & Tutor]
        Norm_FE[Math Term Normalizer (Client)]
        Aria[Screen Reader Layer (NVDA/TalkBack)]
    end

    subgraph Backend ["Backend (FastAPI Engine)"]
        API[FastAPI REST & SSE Router]
        Auth[Firebase Admin RBAC Guard]
        Parser[Docx & PDF Parser]
        Norm_BE[Math Normalizer (Server)]
        OCR[GCV + pix2tex OCR Pipeline]
        Clarifier[AI Clarifier Engine]
        Tutor[Socratic Tutor Engine]
    end

    subgraph External ["Layanan AI & Database"]
        FB[Firebase Auth & Firestore]
        Gemini[Google Gemini 2.0 Flash]
        PG[(PostgreSQL 16)]
        RD[(Redis 7 & Celery)]
    end

    G -->|Unggah Modul DOCX/PDF| UI_G
    UI_G -->|API Upload| API
    API --> Auth
    Auth --> FB
    API --> Parser
    Parser -.->|Dokumen Pindaian| OCR
    Parser --> Clarifier
    Clarifier -->|Prompt Leksikon Baku| Gemini
    Clarifier -->|Simpan Ekspresi & Draf| PG
    UI_G -->|Review & Setujui Narasi| API
    API -->|Terbitkan Modul| PG

    S -->|Akses Keyboard / Screen Reader| UI_S
    UI_S --> Aria
    S -->|Push-to-Talk Pertanyaan| Norm_FE
    Norm_FE -->|Tanya Tutor| API
    API --> Norm_BE
    Norm_BE --> Tutor
    Tutor -->|Metode Sokrates| Gemini
    Tutor -->|Jawaban Bimbingan| UI_S
```

---

## 💻 Tech Stack

| Layer | Teknologi | Versi | Peran & Keterangan |
|---|---|---|---|
| **Frontend Core** | Next.js (App Router, React 19) | `16.3.5` / `19.2.8` | Server-Side Rendering, routing, dan optimasi performa web |
| **Language** | TypeScript | `5.x` | Type-safety penuh pada seluruh antarmuka dan API client |
| **Styling** | Tailwind CSS | `4.x` | Sistem token desain, tata letak adaptif, dan tema aksesibel |
| **A11y Primitives** | React Aria Components | `1.21.1` | Komponen ramah pembaca layar, keyboard focus trapping, dan ARIA attributes |
| **Math Engine** | MathJax Full | `3.2.1` | Rendering matematis berkecepatan tinggi dengan bypass suara bawaan |
| **Backend Core** | FastAPI | `>= 0.115.0` | Framework asinkron berkecepatan tinggi untuk REST API & SSE |
| **Database ORM** | SQLAlchemy + asyncpg | `>= 2.0.40` | Async relational database abstraction layer |
| **Migrations** | Alembic | `>= 1.15.0` | Pengelolaan migrasi skema database relasional |
| **Database** | PostgreSQL | `16` | Penyimpanan persisten dokumen, rumus, narasi, dan modul |
| **Cache & Queue** | Redis + Celery | `7.x` / `>= 5.4.0` | Antrean tugas latar belakang pemrosesan dokumen dan rate limiting |
| **Autentikasi** | Firebase Auth + Firestore | `12.19.0` (Client) / `7.5.0` (Admin) | Manajemen identitas, profil pengguna, dan token JWT verification |
| **Generative AI** | Google Gemini 2.0 Flash | via `google-genai` | Pembangkitan narasi matematis baku dan tutor interaktif Sokrates |
| **OCR & Vision** | Google Cloud Vision + pix2tex | `>= 3.8.0` / `>= 0.1.0` | Deteksi layout teks dan translasi rumus visual menjadi LaTeX |
| **Testing** | pytest, Vitest, Playwright | Modern | Pengujian unit, integrasi, aksesibilitas (@axe-core), dan E2E |

---

## 📁 Struktur Repositori

```
inklusifMath/
├── docs/                             # Dokumen konstitusi arsitektur & desain
│   ├── context.md                    # Single Source of Truth status teknis & checklist
│   ├── leksikon_matematika_baku.md   # 50+ entri narasi standar matematika Indonesia
│   ├── prd_ai_friendly_inklusifmath.md # Product Requirements Document
│   ├── srs_inklusifmath.md           # Software Requirements Specification
│   └── tdd_inklusifmath.md           # Technical Design Document
│
├── frontend/                         # Aplikasi Next.js 16 (Client & SSR)
│   ├── src/
│   │   ├── app/                      # App Router: layout, auth, dashboard, modules, upload
│   │   ├── components/               # Komponen UI aksesibel (Header, TutorModal, MathRenderer)
│   │   ├── hooks/                    # Custom hooks (useTutor, useModules, useNarrations)
│   │   ├── lib/                      # Firebase client, normalizer, audio earcon, API wrapper
│   │   └── types/                    # Definisi tipe TypeScript
│   ├── e2e/                          # Pengujian menyeluruh Playwright & audit aksesibilitas
│   ├── vitest.config.ts              # Konfigurasi pengujian unit Vitest
│   └── package.json
│
├── backend/                          # Aplikasi FastAPI (Engine & Microservices)
│   ├── app/
│   │   ├── api/v1/                   # REST API endpoints (auth, documents, modules, tutor, stt)
│   │   ├── core/                     # Konfigurasi Pydantic, database async, dependencies RBAC
│   │   ├── models/                   # Model SQLAlchemy (User, Document, MathExpression, Module)
│   │   ├── schemas/                  # Schema validasi Pydantic v2
│   │   └── services/                 # Logika bisnis: Document, Tutor, Math Normalizer, OCR
│   ├── alembic/                      # Skrip migrasi skema database
│   ├── tests/                        # Suite pengujian komprehensif pytest (>360 unit tests)
│   ├── Dockerfile                    # Image backend API
│   ├── Dockerfile.worker             # Image worker Celery
│   └── requirements.txt              # Dependensi Python
│
├── nginx/                            # Konfigurasi reverse proxy produksi & SSL
├── docker-compose.yml                # Konfigurasi PostgreSQL 16 & Redis 7 lokal
├── docker-compose.prod.yml           # Konfigurasi deployment kontainer produksi penuh
├── firestore.rules                   # Aturan keamanan database Cloud Firestore
└── README.md                         # Dokumentasi panduan proyek
```

---

## ⚙️ Prasyarat Sistem

Pastikan perangkat Anda telah terpasang:
- **Node.js**: versi `20.x` atau lebih baru
- **Python**: versi `3.12+` (direkomendasikan `3.12` s.d. `3.14`)
- **Docker & Docker Compose**: untuk menjalankan PostgreSQL dan Redis lokal
- **Git**

---

## 🚀 Panduan Instalasi Lokal (Quick Start)

### 1. Clone Repository

```bash
git clone https://github.com/Alfiyansya/inklusifMath.git
cd inklusifMath
```

### 2. Menjalankan Database & Cache (Docker)

Jalankan service database PostgreSQL dan cache Redis menggunakan Docker Compose:

```bash
docker compose up -d
```

Pastikan container aktif dengan memeriksa status:
```bash
docker compose ps
```
- PostgreSQL berjalan pada port `5432`
- Redis berjalan pada port `6379`

---

### 3. Setup Backend (FastAPI)

1. Buka terminal baru dan masuk ke direktori `backend`:
   ```bash
   cd backend
   ```

2. Buat dan aktifkan *virtual environment* Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Untuk Windows: .venv\Scripts\activate
   ```

3. Instal dependensi:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Konfigurasi berkas environment:
   ```bash
   cp .env.example .env
   ```
   *Edit berkas `.env` dan masukkan kredensial `GEMINI_API_KEY`, konfigurasi Firebase, dan layanan terkait.*

5. Jalankan migrasi database:
   ```bash
   alembic upgrade head
   ```

6. Jalankan server backend:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

- Backend API siap di: `http://localhost:8000`
- Dokumentasi interaktif Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

### 4. Setup Background Worker (Celery) [Opsional]

Untuk memproses dokumen berukuran besar secara asinkron di latar belakang:

```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

---

### 5. Setup Frontend (Next.js)

1. Buka terminal baru dan masuk ke direktori `frontend`:
   ```bash
   cd frontend
   ```

2. Instal dependensi Node.js:
   ```bash
   npm install
   ```

3. Konfigurasi berkas environment:
   ```bash
   cp .env.example .env.local
   ```
   *Sesuaikan konfigurasi Firebase Client SDK di dalam `.env.local`.*

4. Jalankan server pengembang:
   ```bash
   npm run dev
   ```

Aplikasi web dapat diakses langsung melalui browser di: `http://localhost:3000`

---

## 🔑 Konfigurasi Environment Variables

### Backend (`backend/.env`)

| Variabel | Deskripsi | Default / Contoh |
|---|---|---|
| `DATABASE_URL` | Koneksi database PostgreSQL async | `postgresql+asyncpg://postgres:postgres@localhost:5432/inklusifmath` |
| `REDIS_URL` | URL instance Redis untuk cache & rate limiter | `redis://localhost:6379/0` |
| `FIREBASE_PROJECT_ID` | ID proyek Firebase Console | `inklusifmath-6d7e9` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path ke JSON Service Account Firebase/GCP | `/path/to/service-account.json` |
| `GEMINI_API_KEY` | API Key Google AI Studio / Vertex AI | `AIzaSy...` |
| `GEMINI_MODEL` | Varian model LLM yang digunakan | `gemini-2.0-flash` |
| `GCV_OCR_ENABLED` | Aktifkan OCR Google Cloud Vision | `true` |
| `MATHPIX_ENABLED` | Aktifkan OCR cadangan Mathpix | `false` |
| `MAX_UPLOAD_SIZE_MB` | Batas maksimum ukuran berkas unggahan | `20` |
| `UPLOAD_DIR` | Direktori lokal penyimpanan sementara | `uploads` |
| `CORS_ORIGINS` | Daftar origin yang diizinkan | `["http://localhost:3000"]` |

### Frontend (`frontend/.env.local`)

| Variabel | Deskripsi | Nilai Contoh |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | URL endpoint backend FastAPI | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | API Key Firebase Web Client | `AIzaSy...` |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Domain autentikasi Firebase | `inklusifmath-6d7e9.firebaseapp.com` |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | ID Proyek Firebase | `inklusifmath-6d7e9` |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Bucket Cloud Storage | `inklusifmath-6d7e9.firebasestorage.app` |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Sender ID Firebase Cloud Messaging | `699742854764` |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | App ID Firebase Web | `1:699742854764:web:...` |

---

## 🧪 Pengujian (Testing & QA)

InklusifMath menerapkan protokol pengujian ketat di seluruh tingkatan aplikasi untuk menjamin kestabilan dan aksesibilitas:

### Backend Tests (Pytest)
Menjalankan suite pengujian unit dan integrasi backend (>360 tes):
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests (Vitest)
Menjalankan pengujian unit komponen, normalizer, dan API client:
```bash
cd frontend
npm run test
```
Untuk menguji cakupan kode (*coverage*):
```bash
npm run test:coverage
```

### End-to-End & Aksesibilitas (Playwright & Axe-Core)
Memastikan seluruh alur pengguna dan kepatuhan WCAG 2.2 AA terverifikasi:
```bash
cd frontend
npm run test:e2e
```

---

## ♿ Standar Aksesibilitas & Pintasan Keyboard

InklusifMath dirancang dengan kepatuhan terhadap standar **WCAG 2.2 Level AA** dan **WAI-ARIA 1.2**.

### Prinsip Utama
- **Indikator Fokus Kontras Tinggi**: Semua elemen interaktif memiliki garis fokus minimal $3:1$ terhadap latar belakang.
- **Skip to Main Content**: Memungkinkan pengguna melompati navigasi header langsung ke konten inti (`WCAG 2.4.1`).
- **Live Regions (`aria-live`)**: Pengumuman status asinkron (seperti status unggahan dokumen dan pemuatan AI) disampaikan tanpa memindahkan fokus pengguna.
- **Semantic HTML**: Menggunakan tag `<main>`, `<nav>`, `<article>`, `<header>` yang terstruktur rapi untuk kemudahan orientasi pembaca layar.

### Pintasan Keyboard (*Keyboard Shortcuts*)

| Pintasan | Lokasi | Fungsi |
|---|---|---|
| <kbd>Alt</kbd> + <kbd>T</kbd> | Global / Pembaca Modul | Membuka dialog **Socratic AI Tutor** secara langsung |
| <kbd>J</kbd> | Pembaca Modul | Berpindah ke ekspresi rumus matematika berikutnya (*Next Formula*) |
| <kbd>K</kbd> | Pembaca Modul | Berpindah ke ekspresi rumus matematika sebelumnya (*Previous Formula*) |
| <kbd>Space</kbd> (Hold) | Dialog AI Tutor | *Push-to-Talk*: Tahan untuk mulai merekam pertanyaan suara |
| <kbd>Esc</kbd> | Modal / Dialog | Menutup dialog dan mengembalikan fokus keyboard ke tombol pemanggil |
| <kbd>Tab</kbd> / <kbd>Shift</kbd>+<kbd>Tab</kbd> | Seluruh Halaman | Menavigasi elemen interaktif secara berurutan |

---

## 🚢 Deployment Produksi

Tersedia konfigurasi produksi siap pakai berbasis Docker Compose dan Nginx:

```bash
# Salin konfigurasi environment produksi
cp .env.prod.example .env

# Jalankan seluruh service (Nginx, Web, API, Worker, Database, Redis)
docker compose -f docker-compose.prod.yml up -d --build
```

Arsitektur produksi mencakup:
- Reverse Proxy Nginx dengan kompresi Gzip dan *security headers* modern.
- Background worker Celery terisolasi untuk pemrosesan dokumen intensif.
- Skrip migrasi database otomatis dijalankan sebelum backend aktif.

---

## 📚 Dokumentasi Terkait

Pelajari lebih lanjut detail perancangan teknis di dalam direktori `/docs`:
- 📖 [Context Document (Single Source of Truth)](docs/context.md)
- 📐 [Leksikon Matematika Baku Indonesia](docs/leksikon_matematika_baku.md)
- 📑 [Product Requirements Document (PRD)](docs/prd_ai_friendly_inklusifmath.md)
- 📋 [Software Requirements Specification (SRS)](docs/srs_inklusifmath.md)
- 🏗️ [Technical Design Document (TDD)](docs/tdd_inklusifmath.md)

---

## 📄 Lisensi

Hak Cipta © 2026 InklusifMath Team. Seluruh hak cipta dilindungi undang-undang (*Private — All Rights Reserved*).
