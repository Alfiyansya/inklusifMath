# Software Requirements Specification (SRS)
## InklusifMath Platform

**Versi:** 1.0  
**Status:** Draft turunan dari PRD v2.0-draft  
**Bahasa:** Indonesia  
**Dokumen sumber utama:** `prd_ai_friendly_inklusifmath.md`

---

## 1. Pendahuluan

### 1.1 Tujuan Dokumen
Dokumen ini mendefinisikan kebutuhan perangkat lunak untuk InklusifMath Platform, yaitu platform e-learning matematika berbasis web yang aksesibel bagi siswa tunanetra total dan low vision di Indonesia. SRS ini menurunkan kebutuhan sistem dari PRD menjadi spesifikasi yang lebih operasional untuk tim produk, desain, engineering, QA, dan AI/ML.

### 1.2 Ruang Lingkup Sistem
InklusifMath adalah platform yang memungkinkan guru mengunggah materi matematika dalam format DOCX atau PDF, memproses materi tersebut menjadi modul web semantik yang kompatibel dengan screen reader native, lalu menyediakan tutor AI kontekstual berbasis push-to-talk bagi siswa tanpa menimbulkan audio collision.

Sistem mencakup:
- ingestion dokumen guru,
- parsing struktur dokumen dan elemen matematika,
- generasi narasi verbal matematika berbasis AI,
- review dan approval oleh guru,
- publikasi modul semantik untuk siswa,
- tutor AI sokrates yang menjaga fokus baca,
- earcon non-verbal untuk status interaksi.

Sistem tidak mencakup kuis interaktif tradisional, TTS internal untuk membacakan materi, maupun materi di luar matematika dasar sampai pengantar aljabar.

### 1.3 Definisi dan Istilah
- **Screen reader native:** pembaca layar yang dipakai pengguna pada OS/perangkat, seperti NVDA, JAWS, VoiceOver, dan TalkBack.
- **Audio collision:** benturan antara suara screen reader dengan audio/TTS internal aplikasi.
- **Semantic clarifier:** komponen AI yang mengubah notasi matematika menjadi narasi verbal baku bahasa Indonesia.
- **Socratic tutor:** tutor AI yang memberi pertanyaan/petunjuk pemandu singkat sesuai konteks aktif.
- **Dual-layer representation:** representasi visual dan semantik dari ekspresi matematika dalam satu modul.
- **Earcon:** sinyal audio sintetis non-verbal untuk status sistem.
- **Live region:** area ARIA yang memungkinkan screen reader mengumumkan perubahan konten.

### 1.4 Referensi
- Product Requirements Document (PRD): InklusifMath Platform v2.0-draft
- WCAG 2.2 Level AA
- WAI-ARIA 1.2

---

## 2. Deskripsi Umum

### 2.1 Perspektif Produk
InklusifMath adalah aplikasi web responsif yang berjalan pada browser desktop dan mobile. Sistem berperan sebagai platform agregator materi matematika aksesibel, bukan LMS penuh. Sistem memproses dokumen guru menjadi modul HTML semantik yang dibaca oleh screen reader pengguna.

### 2.2 Tujuan Produk
Sistem harus:
- menghilangkan audio collision,
- meningkatkan kejelasan pembacaan notasi matematika,
- menurunkan beban kognitif saat belajar matematika digital,
- menjaga kemandirian siswa tunanetra dalam membaca materi,
- mempertahankan guru sebagai validator akhir terhadap hasil AI.

### 2.3 Profil Pengguna

#### 2.3.1 Guru Matematika
Karakteristik:
- mengunggah materi,
- meninjau hasil AI,
- mengedit narasi matematika,
- menyetujui publikasi modul.

#### 2.3.2 Siswa Tunanetra Total
Karakteristik:
- mengandalkan keyboard dan screen reader,
- menavigasi materi lewat heading, paragraf, dan struktur semantik,
- menggunakan tutor via shortcut global dan push-to-talk.

#### 2.3.3 Siswa Low Vision
Karakteristik:
- membutuhkan tampilan visual yang jelas,
- tetap membutuhkan struktur semantik, fokus terlihat, dan target interaksi yang memadai.

### 2.4 Batasan Ruang Lingkup
Sistem hanya mendukung:
- matematika dasar sampai pengantar aljabar,
- input DOCX, PDF teks digital, dan PDF scan/image-based PDF melalui fallback OCR,
- modul pembelajaran semantik berbasis web.

Sistem tidak mendukung:
- kuis interaktif tradisional seperti drag-and-drop dan timer,
- TTS internal untuk isi materi,
- file gambar langsung (JPG, PNG, BMP, TIFF) atau foto dari kamera sebagai input dokumen,
- materi matematika lanjutan di luar cakupan PRD.

### 2.5 Asumsi dan Ketergantungan
- pengguna siswa telah memiliki screen reader native yang aktif pada perangkatnya,
- browser modern mendukung HTML5 semantik, ARIA, MediaDevices API, dan Web Audio API,
- layanan AI dan OCR tersedia sesuai konfigurasi backend,
- kualitas dokumen sumber cukup baik untuk diproses parser atau OCR fallback.

---

## 3. Prinsip Desain Sistem

Sistem harus mengikuti prinsip berikut:
- **Web Standards First**: utamakan HTML semantik dan ARIA yang tepat.
- **Zero Audio Collision**: sistem tidak membacakan isi materi melalui TTS internal.
- **Human-in-the-Loop**: narasi AI wajib dapat ditinjau dan disetujui guru.
- **Low Friction Interaction**: hindari pola interaksi yang membingungkan fokus dan menaikkan beban kognitif.
- **Leksikon Matematika Baku**: narasi matematika harus konsisten dan tidak ambigu dalam bahasa Indonesia.

---

## 4. Arsitektur Tingkat Tinggi

### 4.1 Komponen Utama
Sistem terdiri dari:
1. Antarmuka guru untuk upload, review, edit, dan publish.
2. Pipeline ingestion dan parsing dokumen.
3. Engine AI Math-to-Speech Semantic Clarifier.
4. Mesin transformasi modul ke HTML semantik.
5. Antarmuka pembelajaran siswa.
6. Socratic Context-Aware Tutor.
7. Sistem earcon berbasis Web Audio API.
8. Backend layanan orkestrasi, penyimpanan, dan integrasi AI/OCR.

### 4.2 Alur Utama Sistem
1. Guru mengunggah dokumen.
2. Sistem memvalidasi tipe file.
3. Sistem mengekstrak teks dan struktur dokumen.
4. Sistem mengidentifikasi notasi matematika.
5. AI menghasilkan narasi verbal matematika.
6. Guru meninjau dan mengedit hasil bila perlu.
7. Guru menyetujui publikasi.
8. Sistem menerbitkan modul web semantik.
9. Siswa membaca modul dengan screen reader native.
10. Siswa dapat membuka tutor dengan `Alt + T` dan bertanya via push-to-talk.

---

## 5. Kebutuhan Antarmuka Eksternal

### 5.1 Antarmuka Pengguna

#### 5.1.1 Portal Guru
Portal guru harus menyediakan:
- halaman login,
- form upload dokumen,
- indikator status proses dokumen,
- tampilan review dua kolom,
- editor narasi AI,
- aksi approve dan publish.

#### 5.1.2 Modul Siswa
Modul siswa harus menyediakan:
- struktur heading dan paragraf yang konsisten,
- tampilan rumus visual untuk low vision/guru,
- representasi semantik untuk screen reader,
- shortcut global tutor,
- dialog tutor yang aksesibel,
- live region untuk jawaban tutor.

### 5.2 Antarmuka Perangkat Keras
Sistem memanfaatkan:
- mikrofon perangkat untuk push-to-talk,
- keyboard untuk semua fungsi utama,
- speaker/headphone untuk earcon dan screen reader pengguna.

### 5.3 Antarmuka Perangkat Lunak
Sistem dapat bergantung pada:
- browser modern desktop/mobile,
- screen reader native pengguna,
- layanan STT: Web Speech API (browser-native, primary) dan faster-whisper (self-hosted, fallback),
- model AI seperti Gemini 1.5 Pro/Flash,
- parser dokumen seperti Mammoth.js, python-docx, PyMuPDF, pdfplumber,
- Google Cloud Vision + Mathpix API sebagai fallback untuk PDF scan/image-based PDF.

### 5.4 Antarmuka Komunikasi
Komunikasi client-server harus menggunakan HTTPS. Interaksi AI, OCR, dan parsing eksternal harus melalui API backend yang terkontrol.

---

## 6. Kebutuhan Fungsional

### 6.1 Manajemen Ingestion Dokumen
**FR-01. Upload dokumen**  
Sistem harus menyediakan antarmuka upload bagi guru untuk DOCX, PDF teks digital, dan PDF scan/image-based PDF.

**FR-02. Validasi jenis dokumen**  
Sistem harus memvalidasi format dokumen dan menerapkan strategi ekstraksi hybrid untuk PDF: PyMuPDF terlebih dahulu, lalu Baidu OCR jika hasil ekstraksi kosong.

**FR-03. Parsing struktur dokumen**  
Sistem harus mengekstrak heading, paragraf, dan elemen matematika dari dokumen valid.

### 6.2 Pemrosesan Semantik Matematika
**FR-04. Generasi narasi matematika**  
Sistem harus menghasilkan narasi verbal baku bahasa Indonesia untuk elemen matematika.

**FR-10. Representasi dual-layer**  
Sistem harus menyajikan rumus dalam bentuk visual dan narasi semantik agar dapat dipahami visual user dan screen reader.

### 6.3 Review dan Approval Guru
**FR-05. Review guru**  
Sistem harus menyediakan portal dua kolom untuk membandingkan bentuk asli dan hasil narasi AI.

**FR-06. Edit manual oleh guru**  
Sistem harus memungkinkan guru mengedit narasi hasil AI sebelum persetujuan.

**FR-07. Persetujuan sebelum publikasi**  
Sistem harus mewajibkan persetujuan guru sebelum modul tersedia untuk siswa.

### 6.4 Publikasi Modul Siswa
**FR-08. Publikasi modul semantik**  
Sistem harus menerbitkan modul sebagai halaman web semantik yang dapat dibaca screen reader.

**FR-09. Navigasi struktur modul**  
Sistem harus menyediakan struktur heading dan paragraf yang konsisten agar siswa dapat menavigasi modul secara mandiri.

### 6.5 Tutor AI Kontekstual
**FR-11. Shortcut global tutor**  
Sistem harus menyediakan shortcut global `Alt + T` untuk membuka tutor dari posisi baca aktif.

**FR-12. Penyimpanan fokus aktif**  
Saat tutor dibuka, sistem harus menyimpan elemen yang sedang aktif atau difokuskan.

**FR-13. Focus trapping dialog**  
Saat tutor aktif, fokus keyboard harus dikunci di dalam dialog tutor sesuai perilaku modal aksesibel.

**FR-14. Push-to-talk**  
Sistem harus mendukung input suara berbasis push-to-talk untuk siswa.

**FR-15. Respons tutor via live region**  
Jawaban tutor harus disalurkan ke region teks kompatibel screen reader, misalnya `aria-live="polite"` atau `role="status"`.

**FR-16. Restorasi fokus**  
Saat dialog tutor ditutup, fokus harus kembali ke elemen yang sebelumnya aktif.

### 6.6 Status Interaksi dan Operabilitas
**FR-17. Earcon status**  
Sistem harus memberi status interaksi melalui earcon sintetis non-verbal.

**FR-18. Operasi penuh via keyboard**  
Semua fungsi utama harus dapat digunakan tanpa mouse.

---

## 7. Kebutuhan Non-Fungsional

### 7.1 Aksesibilitas
Sistem harus:
- memenuhi WCAG 2.2 Level AA,
- menggunakan WAI-ARIA 1.2 secara tepat,
- memastikan semua fungsi dapat dioperasikan via keyboard,
- menjaga fokus keyboard agar tidak hilang atau tertutup,
- menyediakan alternatif semantik untuk konten non-teks termasuk rumus,
- memiliki outline fokus yang terlihat jelas dan berkontras tinggi,
- mendukung kebutuhan pengguna low vision,
- memasukkan audit Axe Core dan Lighthouse Accessibility dalam proses verifikasi.

### 7.2 Kinerja
Sistem ditargetkan memenuhi:
- Focus Disorientation Rate: 0.0%,
- Audio Collision Incidents: 0,
- Math Pronunciation Accuracy: minimal 98% berdasarkan verifikasi guru,
- Time-to-Inquire: rata-rata kurang dari 6 detik dari shortcut ke selesai bicara,
- Earcon latency: kurang dari 15 ms,
- ASR Bahasa Indonesia WER: kurang dari 8% untuk istilah matematika dasar,
- First Contentful Paint modul: kurang dari 1.2 detik,
- skor audit aksesibilitas: 100/100 pada Axe Core dan Lighthouse Accessibility.

### 7.3 Keandalan
- sistem harus menangani kegagalan parsing dan OCR dengan status yang jelas,
- sistem harus menjaga hasil review guru sebelum publikasi,
- sistem harus mencegah publikasi modul tanpa approval guru.

### 7.4 Kegunaan
- respons tutor harus singkat, maksimal 2–3 kalimat,
- siswa tidak boleh dipaksa mengetik pertanyaan matematika panjang jika voice input tersedia,
- target klik/sentuh harus memadai untuk pengguna low vision dan mobile,
- status sistem harus dapat dipahami teknologi asistif.

### 7.5 Maintainability
- arsitektur harus memisahkan ingestion, parsing, AI clarifier, tutor, dan rendering modul,
- aturan leksikon matematika harus dapat diperbarui tanpa mengubah seluruh sistem,
- pipeline parsing harus mendukung penambahan peningkatan extractor di masa depan.

### 7.6 Keamanan dan Privasi
- akses ke fungsi guru harus melalui autentikasi,
- komunikasi data harus melalui HTTPS,
- akses layanan AI/OCR harus dimediasi backend,
- kebijakan retensi data, RBAC rinci, dan audit trail belum dirinci penuh dalam PRD dan perlu dispesifikasikan pada dokumen turunan desain/arsitektur.

---

## 8. Aturan Bisnis

Sistem harus mematuhi aturan berikut:
- hasil AI tidak boleh langsung dipublikasikan tanpa verifikasi guru,
- tutor tidak boleh memberikan audio naratif internal untuk isi materi,
- tutor harus berbasis konteks aktif saat siswa membaca,
- materi yang diproses dibatasi pada matematika dasar sampai pengantar aljabar,
- sistem harus memprioritaskan kompatibilitas dengan screen reader native dibanding interaksi visual kompleks,
- sistem harus menghindari kuis interaktif tradisional yang meningkatkan friksi aksesibilitas.

---

## 9. Model Data Konseptual

### 9.1 Entitas Utama
- **User**: merepresentasikan guru atau siswa.
- **DocumentUpload**: file sumber yang diunggah guru.
- **ParsedContent**: hasil ekstraksi struktur dokumen.
- **MathExpression**: elemen matematika yang terdeteksi.
- **SemanticNarration**: narasi verbal hasil AI untuk MathExpression.
- **ReviewRecord**: hasil edit dan approval guru.
- **LearningModule**: modul semantik yang telah dipublikasikan.
- **TutorSession**: sesi interaksi tutor siswa.
- **TutorMessage**: pertanyaan dan jawaban dalam sesi tutor.
- **EarconEvent**: status non-verbal yang dipicu sistem.

### 9.2 Relasi Umum
- satu guru dapat mengunggah banyak dokumen,
- satu dokumen menghasilkan satu atau lebih parsed content,
- satu parsed content dapat memiliki banyak math expression,
- satu math expression memiliki satu atau lebih semantic narration versi kerja,
- satu learning module hanya dapat dipublikasikan setelah review record disetujui guru,
- satu tutor session terkait dengan satu siswa dan satu konteks modul aktif.

---

## 10. Skenario Operasional Utama

### 10.1 Skenario Guru
1. Guru login ke sistem.
2. Guru mengunggah dokumen.
3. Sistem memvalidasi file dan menjalankan parser.
4. Sistem menghasilkan narasi matematika.
5. Guru meninjau hasil dalam portal dua kolom.
6. Guru mengedit bila perlu.
7. Guru menyetujui hasil.
8. Sistem mempublikasikan modul.

### 10.2 Skenario Siswa
1. Siswa membuka modul pembelajaran.
2. Siswa menavigasi heading dan paragraf dengan screen reader.
3. Saat menemukan rumus, screen reader membaca narasi semantik.
4. Siswa menekan `Alt + T` saat membutuhkan bantuan.
5. Sistem menyimpan fokus aktif dan membuka tutor.
6. Siswa menggunakan push-to-talk untuk bertanya.
7. Sistem mengirim konteks aktif dan transkrip ke tutor AI.
8. Jawaban tutor ditampilkan di live region.
9. Screen reader membacakan jawaban.
10. Saat tutor ditutup, fokus kembali ke elemen sebelumnya.

---

## 11. Batasan Implementasi

Sistem harus mematuhi batasan berikut:
- tidak menggunakan TTS internal untuk membacakan isi materi,
- tidak membangun interaksi utama yang bergantung pada mouse,
- tidak menerbitkan modul tanpa approval guru,
- tidak keluar dari cakupan materi matematika dasar sampai pengantar aljabar,
- tidak mengandalkan satu-satunya strategi ekstraksi PDF tanpa fallback,
- tidak mengorbankan fokus keyboard demi efek UI non-esensial.

---

## 12. Kriteria Penerimaan Tingkat Sistem

Sistem dinyatakan memenuhi SRS apabila:
1. Guru dapat mengunggah DOCX dan PDF, termasuk PDF scan melalui fallback OCR.
2. Sistem mampu mengekstrak struktur dokumen dan notasi matematika.
3. Sistem menghasilkan narasi verbal matematika yang dapat diedit guru.
4. Modul hanya bisa dipublikasikan setelah approval guru.
5. Modul hasil publikasi dapat dibaca screen reader dengan struktur semantik yang konsisten.
6. Tutor dapat dibuka dengan `Alt + T` dari konteks baca aktif.
7. Fokus keyboard tersimpan, terjebak benar di dialog tutor, lalu pulih ke posisi semula saat ditutup.
8. Input pertanyaan suara dapat diproses melalui push-to-talk.
9. Jawaban tutor tampil di live region dan dibacakan screen reader native.
10. Tidak ada audio collision akibat audio naratif internal.
11. Semua fungsi utama dapat dioperasikan hanya dengan keyboard.
12. Audit aksesibilitas dan metrik target utama tercapai sesuai dokumen.

---

## 13. Risiko dan Area yang Perlu Spesifikasi Lanjutan

Area berikut sudah tersirat dalam PRD namun masih memerlukan dokumen turunan lebih rinci:
- kebijakan retensi dan penghapusan data,
- role-based access control yang lebih detail,
- versioning materi dan riwayat revisi guru,
- integrasi institusional seperti LMS/sekolah bila dibutuhkan,
- strategi evaluasi hasil belajar non-quiz,
- matriks kompatibilitas browser, OS, dan screen reader yang diuji resmi.

---

## 14. Roadmap Implementasi yang Diturunkan dari PRD

### Fase 1
Fondasi aksesibel, template modul semantik, parser DOCX, dan audit Axe Core di pipeline.

### Fase 2
AI semantic clarifier, portal review guru dua kolom, dan validasi dual-layer rendering.

### Fase 3
Modal tutor aksesibel, push-to-talk, live region, dan engine earcon.

### Fase 4
Uji lapangan dengan pengguna NVDA, JAWS, dan TalkBack serta audit keamanan dan aksesibilitas akhir.

---

## 15. Penutup

SRS ini menerjemahkan PRD InklusifMath menjadi spesifikasi perangkat lunak yang siap dijadikan dasar desain solusi, backlog engineering, test case QA, dan turunan dokumen teknis berikutnya. Fokus utama sistem tetap pada aksesibilitas semantik, zero audio collision, validasi guru terhadap hasil AI, dan pengalaman belajar matematika yang mandiri bagi siswa tunanetra dan low vision.
