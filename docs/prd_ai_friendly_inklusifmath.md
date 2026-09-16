# Product Requirements Document (PRD)
## InklusifMath Platform
### Versi detail, terstruktur, dan AI-friendly

---

## 1. Metadata Dokumen

- **Nama produk:** InklusifMath Platform
- **Jenis dokumen:** Product Requirements Document (PRD)
- **Versi dokumen:** 2.0-draft
- **Status:** Draft terstruktur berbasis dokumen sumber
- **Target pengguna utama:** Guru matematika dan siswa tunanetra / low vision
- **Target platform:** Web desktop dan mobile browser (responsive)
- **Target standar aksesibilitas:** WAI-ARIA 1.2 dan WCAG 2.2 Level AA
- **Sumber dasar dokumen:**
  - Product Requirements Document (PRD): Platform Agregator E-Learning Matematika Inklusif untuk Siswa Tunanetra
  - Proposal Teknis Platform E-Learning Matematika Inklusif

---

## 2. Ringkasan Eksekutif

InklusifMath Platform adalah platform agregator e-learning matematika berbasis web untuk siswa disabilitas netra di Indonesia, mencakup tunanetra total dan low vision. Platform ini dirancang untuk mengatasi tiga hambatan utama dalam pembelajaran matematika digital yang ada saat ini:

1. **Audio collision** antara screen reader native pengguna dan audio/TTS internal dari website.
2. **Ambiguitas pembacaan notasi matematika** oleh screen reader standar yang tidak memahami struktur matematis secara semantik.
3. **Beban kognitif dan hambatan aksesibilitas** dari kuis interaktif tradisional seperti drag-and-drop, timer, dan form dinamis.

Solusi yang ditawarkan adalah platform yang menerima materi guru dalam format DOCX atau PDF teks digital, lalu memprosesnya menjadi modul web semantik murni yang kompatibel dengan screen reader native. Platform menggunakan dua komponen AI utama:

- **AI Math-to-Speech Semantic Clarifier** untuk menghasilkan narasi verbal baku bahasa Indonesia pada notasi matematika.
- **AI Socratic Context-Aware Tutor** untuk membantu siswa memahami materi melalui interaksi tanya jawab berbasis push-to-talk tanpa merusak fokus baca.

Prinsip inti sistem adalah **Web Standards First**, **Zero Audio Collision**, **Human-in-the-Loop**, dan **pengurangan friksi interaksi**.

---

## 3. Latar Belakang Masalah

### 3.1 Masalah utama di lapangan

Siswa tunanetra dan low vision mengalami hambatan ketika mempelajari matematika melalui platform digital karena:

- Banyak platform memakai audio browser internal yang bertabrakan dengan screen reader native seperti NVDA, JAWS, VoiceOver, dan TalkBack.
- Notasi matematika dasar sering dibacakan secara literal, bukan semantik. Akibatnya, bentuk seperti pecahan, eksponen, dan ekspresi aljabar terdengar ambigu.
- Interaksi e-learning umum seperti kuis berbatas waktu, drag-and-drop, dan popup kompleks sering menyebabkan kehilangan fokus, keyboard trap, dan kelelahan kognitif.

### 3.2 Dampak masalah

Dampak dari masalah tersebut adalah:

- Siswa kesulitan belajar mandiri.
- Guru harus melakukan banyak adaptasi manual.
- Materi matematika tidak tersampaikan secara konsisten.
- Pengalaman belajar menjadi lambat, membingungkan, dan tidak dapat diandalkan.

---

## 4. Visi Produk

Menciptakan ekosistem belajar matematika digital mandiri yang aksesibel, di mana materi guru dapat otomatis diadaptasi ke format yang kompatibel dengan teknologi asistif siswa tanpa interupsi audio buatan browser.

---

## 5. Tujuan Produk

### 5.1 Tujuan utama

1. **Zero Audio Collision**
   Semua narasi materi dan respons sistem harus dapat dibaca melalui screen reader native pengguna, bukan melalui pemutar audio internal web.

2. **Presisi pembacaan rumus**
   Notasi matematika dasar harus memiliki representasi verbal yang tidak ambigu melalui semantic clarifier dan verifikasi guru.

3. **Efisiensi akses bantuan**
   Siswa harus dapat memanggil bantuan tutor dengan cepat melalui shortcut global dan interaksi push-to-talk.

4. **Kepatuhan aksesibilitas penuh**
   Platform harus memenuhi standar WCAG 2.2 Level AA dan dapat digunakan sepenuhnya lewat keyboard serta screen reader.

### 5.2 Sasaran hasil produk

- Modul matematika dapat dibaca mandiri oleh siswa tunanetra.
- Guru dapat mengunggah dan memverifikasi materi tanpa perlu memahami MathML, HTML, atau ARIA secara teknis.
- Respons tutor muncul tanpa menghilangkan posisi fokus baca siswa.
- Materi matematika dasar sampai pengantar aljabar dapat dipublikasikan secara konsisten dan dapat diakses.

---

## 6. Non-Goals

Hal-hal berikut berada di luar cakupan versi ini:

1. **Kuis interaktif dan evaluasi berwaktu**
   Tidak ada multiple choice quiz, drag-and-drop, atau ujian dinamis berbatas waktu.

2. **Cakupan materi lanjutan**
   Platform dibatasi pada matematika dasar hingga pengantar aljabar. Dokumen sumber tidak mendukung kalkulus, geometri ruang kompleks, atau trigonometri lanjutan pada versi ini.

3. **Dukungan file non-dokumen**
   Sistem menolak file gambar langsung (JPG, PNG, BMP, TIFF), foto dari kamera, dan dokumen yang seluruh halamannya berisi grafik atau diagram tanpa teks. PDF yang dihasilkan dari scanner dokumen tetap diterima dan diproses melalui fallback OCR sesuai strategi hybrid extraction (Section 18.3.1).

4. **Mesin TTS internal untuk membacakan materi**
   Platform tidak membangun pemutar audio sintesis internal untuk narasi materi.

---

## 7. Prinsip Desain Produk

1. **Web Standards First**
   Platform mengutamakan HTML semantik, ARIA yang tepat, dan perilaku yang kompatibel dengan screen reader native.

2. **Zero Audio Collision**
   Sistem tidak boleh memaksa suara naratif browser yang bertabrakan dengan screen reader.

3. **Human-in-the-Loop**
   Output AI untuk narasi matematika harus ditinjau dan disetujui guru sebelum dipublikasikan.

4. **Eliminasi friksi aksesibilitas**
   Interaksi yang rentan menimbulkan kebingungan fokus atau beban kognitif harus dihindari.

5. **Leksikon matematika baku bahasa Indonesia**
   AI harus dipandu untuk menggunakan istilah matematika yang konsisten dan tidak ambigu.

---

## 8. Ruang Lingkup Produk

### 8.1 Cakupan pengguna

- **Guru matematika** sebagai pengunggah, peninjau, editor, dan publisher materi.
- **Siswa tunanetra total** sebagai pembaca utama berbasis screen reader.
- **Siswa low vision** sebagai pembaca visual yang tetap membutuhkan aksesibilitas visual dan struktur yang baik.

### 8.2 Cakupan materi

Materi yang didukung mencakup:

- Bilangan bulat
- Pecahan
- Desimal
- Persentase
- KPK / FPB
- Rasio
- Operasi hitung campuran
- Persamaan linear satu variabel sederhana
- Pengantar aljabar dasar

### 8.3 Cakupan format input

- DOCX
- PDF teks digital
- PDF scan / image-based PDF yang diproses melalui fallback OCR bila ekstraksi teks langsung gagal

### 8.4 Cakupan output

- Modul web HTML semantik yang siap dibaca screen reader
- Rumus dengan representasi visual dan narasi semantik
- Bantuan tutor kontekstual berbasis dialog singkat

---

## 9. Persona Pengguna

### 9.1 Persona A — Siswa Tunanetra

**Karakteristik**
- Mengandalkan keyboard dan screen reader.
- Menggunakan NVDA, JAWS, VoiceOver, atau TalkBack.

**Pain points**
- Sering kehilangan fokus saat ada popup atau update konten.
- Sulit mengetik pertanyaan matematika dalam input teks biasa.
- Terganggu jika ada suara web yang bertabrakan dengan screen reader.

**Kebutuhan utama**
- Struktur heading yang jelas.
- Shortcut global yang konsisten.
- Voice input untuk bertanya.
- Penjelasan rumus yang tidak ambigu.

### 9.2 Persona B — Guru Matematika Inklusif

**Karakteristik**
- Mengajar di sekolah inklusi atau SLB-A.
- Terbiasa membuat materi di Microsoft Word atau Google Docs.

**Pain points**
- Tidak menguasai MathML, HTML, ARIA, atau WCAG.
- Tidak punya waktu membuat audio manual untuk setiap materi.

**Kebutuhan utama**
- Upload dokumen yang sederhana.
- Hasil narasi AI yang bisa ditinjau dan diedit.
- Proses publikasi modul yang jelas.

---

## 10. Pernyataan Masalah yang Harus Diselesaikan Sistem

Sistem harus mampu:

1. Menerima materi matematika guru dalam format dokumen teks terstruktur.
2. Mengekstrak struktur teks dan notasi matematika dari dokumen.
3. Menghasilkan narasi verbal matematika yang baku dan tidak ambigu.
4. Menyediakan portal verifikasi guru sebelum modul dipublikasikan.
5. Menampilkan modul dalam bentuk web semantik yang dapat dibaca screen reader native.
6. Menyediakan tutor sokrates yang dapat dipanggil kapan saja tanpa merusak posisi fokus baca.
7. Memberikan status sistem melalui earcon dan status region yang ramah screen reader.

---

## 11. User Journey Utama

### 11.1 Alur guru

1. Guru login.
2. Guru mengunggah DOCX atau PDF teks digital.
3. Backend mengekstrak struktur teks dan notasi matematika.
4. AI semantic clarifier menghasilkan narasi verbal baku.
5. Guru membuka portal review dua kolom.
6. Guru memeriksa dan bila perlu mengedit narasi hasil AI.
7. Guru menyetujui hasil.
8. Sistem mempublikasikan modul untuk siswa.

### 11.2 Alur siswa

1. Siswa membuka modul pembelajaran.
2. Siswa menavigasi heading dan paragraf menggunakan screen reader.
3. Saat menemukan rumus, screen reader membacakan narasi semantik dari rumus tersebut.
4. Jika siswa kesulitan memahami materi, siswa menekan shortcut global `Alt + T`.
5. Sistem menyimpan fokus aktif saat ini.
6. Dialog tutor dibuka dan fokus dikunci di dalam dialog.
7. Siswa menekan dan menahan tombol yang ditentukan untuk push-to-talk.
8. Sistem merekam pertanyaan lisan siswa.
9. Setelah input selesai, AI tutor memproses konteks aktif dan pertanyaan siswa.
10. Respons tutor ditampilkan sebagai teks semantik pada region `aria-live="polite"`.
11. Screen reader membacakan respons tutor.
12. Saat dialog ditutup, fokus kembali ke elemen terakhir yang sedang dibaca siswa.

---

## 12. Fitur Inti Produk

### 12.1 Modul upload materi guru

**Deskripsi**
Guru dapat mengunggah materi dalam format DOCX, PDF teks digital, atau PDF scan yang akan diproses dengan strategi ekstraksi hybrid.

**Input**
- File DOCX
- File PDF teks digital
- File PDF scan / image-based PDF

**Aturan**
- Untuk PDF, sistem harus terlebih dahulu mencoba ekstraksi teks menggunakan PyMuPDF.
- Jika teks berhasil diekstrak, sistem melanjutkan proses tanpa OCR.
- Jika hasil ekstraksi kosong, sistem harus memperlakukan file sebagai PDF scan / image-based PDF dan meneruskannya ke Baidu OCR.
- Sistem harus memprioritaskan integritas struktur dokumen.

**Output**
- Data struktur konten untuk diproses parser dan AI.

### 12.2 Engine parser dokumen

**Deskripsi**
Sistem mengekstrak heading, paragraf, dan notasi matematika dari dokumen sumber.

**Fungsi utama**
- Ekstraksi struktur teks
- Ekstraksi OMML / LaTeX / notasi matematika yang tersedia pada dokumen
- Persiapan konten untuk dual-layer representation

### 12.3 AI Math-to-Speech Semantic Clarifier

**Deskripsi**
AI menghasilkan narasi verbal baku bahasa Indonesia untuk rumus dan simbol matematika agar dapat dibacakan screen reader tanpa ambigu.

**Tujuan**
- Menghilangkan ambiguitas pembacaan formula
- Menstandarkan istilah matematika
- Mendukung guru dalam proses kurasi

**Batasan**
- Output AI tidak langsung dipublikasikan tanpa verifikasi guru.
- Cakupan materi dibatasi pada matematika dasar hingga pengantar aljabar.

### 12.4 Portal verifikasi guru

**Deskripsi**
Guru meninjau hasil konversi AI sebelum publikasi.

**Komponen utama**
- Kolom kiri: tampilan visual materi dan rumus asli
- Kolom kanan: narasi verbal hasil AI yang bisa diedit
- Tombol approve / publish

**Tujuan**
- Menjamin akurasi semantik
- Menempatkan guru sebagai peninjau akhir

### 12.5 Modul pembelajaran siswa

**Deskripsi**
Materi diterbitkan sebagai halaman web semantik yang dibaca menggunakan screen reader native siswa.

**Syarat utama**
- Struktur heading jelas
- Rumus memiliki narasi semantik
- Tidak ada audio naratif internal untuk isi materi

### 12.6 Socratic Context-Aware Tutor

**Deskripsi**
Tutor AI membantu siswa memahami konsep melalui pertanyaan pemandu, bukan jawaban panjang langsung.

**Karakter output**
- Singkat
- Kontekstual terhadap bagian materi aktif
- Maksimal 2–3 kalimat sesuai dokumen sumber
- Disalurkan sebagai teks ke `aria-live="polite"`

**Cara akses**
- Shortcut global `Alt + T`
- Input pertanyaan melalui push-to-talk

### 12.7 Sistem earcon

**Deskripsi**
Sistem memberi status non-verbal menggunakan nada sintetis berbasis Web Audio API.

**Fungsi**
- Konfirmasi mulai rekam
- Konfirmasi selesai rekam
- Penanda jawaban siap
- Penanda error / kegagalan

**Tujuan**
- Memberi status tanpa menambah beban verbal pada screen reader

---

## 13. Kebutuhan Fungsional

### FR-01 Upload dokumen
Sistem harus menyediakan antarmuka upload bagi guru untuk DOCX, PDF teks digital, dan PDF scan / image-based PDF.

### FR-02 Validasi jenis dokumen
Sistem harus memvalidasi format dokumen dan menerapkan strategi ekstraksi hybrid untuk PDF: coba PyMuPDF terlebih dahulu, lalu gunakan Baidu OCR jika hasil ekstraksi teks kosong.

### FR-03 Parsing struktur dokumen
Sistem harus mengekstrak heading, paragraf, dan elemen matematika dari dokumen yang valid, baik dari hasil ekstraksi langsung maupun dari fallback OCR.

### FR-04 Generasi narasi matematika
Sistem harus menghasilkan narasi verbal baku bahasa Indonesia untuk elemen matematika yang ditemukan.

### FR-05 Review guru
Sistem harus menyediakan portal dua kolom agar guru dapat membandingkan bentuk asli dan hasil narasi AI.

### FR-06 Edit manual oleh guru
Sistem harus memungkinkan guru mengedit narasi hasil AI sebelum persetujuan.

### FR-07 Persetujuan sebelum publikasi
Sistem harus mewajibkan persetujuan guru sebelum modul tersedia untuk siswa.

### FR-08 Publikasi modul semantik
Sistem harus menerbitkan modul sebagai halaman web semantik yang dapat dibaca screen reader.

### FR-09 Navigasi struktur modul
Sistem harus menyediakan struktur heading dan paragraf yang konsisten agar siswa dapat menavigasi modul secara mandiri.

### FR-10 Representasi dual-layer
Sistem harus menyajikan rumus dalam bentuk visual untuk guru/low vision dan dalam bentuk narasi semantik untuk screen reader.

### FR-11 Shortcut global tutor
Sistem harus menyediakan shortcut global `Alt + T` untuk membuka tutor dari posisi baca aktif.

### FR-12 Penyimpanan fokus aktif
Saat tutor dibuka, sistem harus menyimpan elemen yang sedang aktif / difokuskan.

### FR-13 Focus trapping dialog
Saat tutor aktif, fokus keyboard harus dikunci di dalam dialog tutor sesuai perilaku modal aksesibel.

### FR-14 Push-to-talk
Sistem harus mendukung input suara berbasis push-to-talk untuk siswa.

### FR-15 Respons tutor via live region
Jawaban tutor harus disalurkan ke region teks yang kompatibel dengan screen reader, misalnya `aria-live="polite"` atau `role="status"`.

### FR-16 Restorasi fokus
Saat dialog tutor ditutup, fokus harus kembali ke elemen yang sebelumnya aktif.

### FR-17 Earcon status
Sistem harus memberi status interaksi melalui earcon sintetis non-verbal.

### FR-18 Operasi penuh via keyboard
Semua fungsi utama harus dapat digunakan tanpa mouse.

---

## 14. Kebutuhan Interaksi dan UX

1. Siswa tidak boleh dipaksa mengetik pertanyaan matematika panjang di field teks biasa jika voice input tersedia.
2. Dialog tutor harus mudah dibuka dari konteks mana pun saat membaca modul.
3. Tutor tidak boleh membuat siswa kehilangan posisi baca.
4. Respons tutor harus pendek agar tidak membebani memori pendengaran.
5. Update status sistem harus dapat dipahami teknologi asistif.
6. Elemen interaktif harus memiliki indikator fokus yang jelas.
7. Target klik/sentuh harus cukup besar untuk pengguna low vision dan mobile.

---

## 15. Kebutuhan Aksesibilitas

Platform harus memenuhi kebutuhan berikut:

- Semua fungsi dapat dioperasikan via keyboard.
- Fokus keyboard tidak boleh tertutup atau hilang.
- Status sistem harus diumumkan dengan cara yang kompatibel dengan screen reader.
- Konten non-teks, termasuk rumus, harus memiliki alternatif semantik.
- Tampilan harus mendukung kebutuhan pengguna low vision.
- Struktur halaman harus semantik dan konsisten.

### Kriteria implementasi yang ditegaskan dokumen sumber

- Shortcut global tutor tersedia.
- Outline fokus terlihat jelas dan berkontras tinggi.
- Respons tutor disalurkan ke region status / live region.
- Tombol kontrol memiliki ukuran target minimum yang memadai.
- Audit Axe Core dan Lighthouse Accessibility menjadi bagian dari verifikasi.

---

## 16. Spesifikasi Perilaku Tutor AI

### 16.1 Tujuan tutor
Tutor bertugas membantu siswa memahami konsep yang sedang dibaca melalui pendekatan sokrates.

### 16.2 Input tutor
- Konteks bacaan aktif
- Posisi fokus aktif pengguna
- Transkripsi suara siswa
- Identitas modul / bagian materi

### 16.3 Output tutor
- Teks semantik singkat
- Bersifat pemandu
- Tidak berupa audio naratif internal
- Dibacakan oleh screen reader native melalui live region

### 16.4 Batasan tutor
- Maksimal 2–3 kalimat
- Menggunakan leksikon baku bahasa Indonesia
- Fokus pada konteks bacaan aktif
- Mengurangi beban dengar dan beban kognitif

---

## 17. Representasi Konten Matematika

Platform menggunakan pendekatan **dual-layer representation**:

1. **Layer visual**
   Digunakan untuk guru dan pengguna low vision, dirender dengan MathML native atau MathJax sesuai dokumen sumber.

2. **Layer semantik**
   Digunakan untuk screen reader, diwujudkan melalui narasi verbal baku pada atribut seperti `aria-label`.

Tujuan pendekatan ini adalah agar satu ekspresi matematika tetap dapat dipahami baik secara visual maupun secara auditif tanpa ambigu.

---

## 18. Kebutuhan Teknis Tingkat Tinggi

### 18.1 Frontend
- HTML5 semantik murni atau React aksesibel
- JavaScript / TypeScript
- Web Audio API untuk earcon
- MediaDevices API untuk push-to-talk
- ARIA live region untuk output tutor

### 18.2 Backend
- Node.js atau Python FastAPI
- Layanan parsing dokumen
- Layanan AI clarifier
- Layanan tutor AI

### 18.3 Tools parsing yang disebut dokumen sumber
- Mammoth.js
- python-docx
- PyMuPDF
- pdfplumber
- Baidu OCR sebagai fallback untuk PDF scan / image-based PDF

### 18.3.1 Strategi ekstraksi PDF hybrid
- Langkah 1: coba ekstraksi teks PDF menggunakan PyMuPDF terlebih dahulu.
- Langkah 2: jika teks berhasil diekstrak, proses parsing dilanjutkan tanpa OCR.
- Langkah 3: jika hasil ekstraksi kosong, file diperlakukan sebagai PDF scan / image-based PDF.
- Langkah 4: file diteruskan ke Baidu OCR untuk ekstraksi teks.
- Langkah 5: hasil OCR masuk kembali ke pipeline parsing struktur dan elemen matematika.

### 18.4 Speech dan AI yang disebut dokumen sumber
- Whisper API atau Vosk Indo untuk speech-to-text
- Gemini 1.5 Pro atau Flash untuk semantic clarifier dan tutor

---

## 19. Metrik Keberhasilan

### 19.1 Metrik UX dan aksesibilitas
- **Focus Disorientation Rate:** 0.0%
- **Audio Collision Incidents:** 0
- **Math Pronunciation Accuracy:** >= 98% berdasarkan verifikasi guru
- **Time-to-Inquire:** rata-rata < 6 detik dari shortcut ke selesai bicara

### 19.2 Metrik teknis
- **Earcon latency:** < 15 ms
- **ASR Bahasa Indonesia WER:** < 8% untuk istilah matematika dasar
- **First Contentful Paint modul:** < 1.2 detik
- **Audit aksesibilitas:** 100/100 pada Axe Core dan Lighthouse Accessibility

---

## 20. Roadmap Produk

### Fase 1 — Fondasi aksesibel dan parser dokumen
- Membangun template modul semantik sesuai WCAG 2.2 AA
- Membangun parser DOCX
- Menambahkan pengujian Axe Core ke CI/CD

### Fase 2 — Semantic clarifier dan portal guru
- Mengembangkan AI math-to-speech clarifier
- Membangun antarmuka review dua kolom
- Menguji dual-layer rendering

### Fase 3 — Tutor sokrates dan earcon
- Membangun engine earcon dengan Web Audio API
- Membangun modal tutor yang aksesibel
- Mengintegrasikan push-to-talk dan live region

### Fase 4 — Uji coba lapangan
- Uji dengan siswa tunanetra pengguna NVDA, JAWS, dan TalkBack
- Kalibrasi mikrofon dan ASR
- Audit keamanan data dan sertifikasi aksesibilitas

---

## 21. Risiko yang Sudah Tersirat dari Dokumen Sumber

1. **Risiko ambiguitas matematika**
   Diatasi dengan semantic clarifier dan verifikasi guru.

2. **Risiko audio collision**
   Diatasi dengan tidak memakai TTS internal untuk materi.

3. **Risiko kehilangan fokus saat interaksi tutor**
   Diatasi dengan focus trapping dan restorasi fokus.

4. **Risiko beban kognitif tinggi**
   Diatasi dengan respons tutor singkat dan penghapusan kuis interaktif tradisional.

5. **Risiko kualitas dokumen sumber rendah**
   Diatasi dengan pembatasan hanya pada DOCX dan PDF teks digital.

---

## 22. Batasan dan Hal yang Belum Dirinci Penuh di Dokumen Sumber

Berdasarkan penelaahan terhadap dua dokumen sumber, beberapa area penting memang sudah tersirat sebagai kebutuhan lanjutan, tetapi **belum memiliki spesifikasi operasional yang cukup** untuk langsung dibawa ke implementasi. Karena itu, area-area berikut ditandai sebagai **belum ditentukan** atau **belum lengkap** dalam PRD ini.

1. **Kebijakan retensi data suara dan transkrip**  
   Dokumen sumber menjelaskan adanya interaksi suara berbasis push-to-talk pada tutor AI, tetapi tidak menjelaskan apakah audio mentah disimpan, berapa lama transkrip dipertahankan, apakah transkrip dipakai untuk pelatihan model, bagaimana mekanisme penghapusan data, serta apakah ada perbedaan retensi antara data siswa, guru, dan log sistem. Artinya, aspek tata kelola data percakapan masih kosong dan perlu diturunkan menjadi kebijakan privasi, keamanan, dan kepatuhan operasional.

2. **Model otorisasi per peran yang lebih rinci**  
   Kedua dokumen sudah membedakan peran utama seperti guru, siswa, dan administrator secara implisit melalui alur kerja, tetapi belum merinci matriks izin per aksi. Belum dijelaskan siapa yang boleh membuat, mengedit, mereview, mempublikasikan, menarik kembali, mengarsipkan, atau menghapus materi; siapa yang boleh melihat log verifikasi AI; serta apakah ada pemisahan hak akses antara admin teknis, admin akademik, dan reviewer konten. Tanpa detail ini, desain kontrol akses berbasis peran belum siap diimplementasikan secara aman.

3. **Versioning konten setelah publikasi**  
   Dokumen sumber menjelaskan alur unggah, proses AI, verifikasi guru, dan publikasi, tetapi tidak menjelaskan apa yang terjadi setelah materi yang sudah tayang perlu diperbarui. Belum ada aturan tentang nomor versi, riwayat perubahan, perbandingan antarversi, rollback, notifikasi perubahan ke pengguna, maupun status materi ketika revisi sedang berlangsung. Ini berarti siklus hidup konten pascapublikasi masih belum terdefinisi.

4. **Detail integrasi kelas / sekolah / administrasi institusi**  
   Fokus dokumen masih pada platform, aksesibilitas, dan pipeline konten, bukan pada operasi institusional. Karena itu belum ada spesifikasi tentang struktur sekolah, kelas, semester, roster siswa, penugasan guru ke kelas, sinkronisasi dengan sistem akademik sekolah, atau model multi-tenant antarinstansi. Belum juga dijelaskan apakah produk diposisikan per sekolah, per yayasan, atau sebagai platform lintas institusi dengan isolasi data masing-masing. Area ini penting bila produk akan dipakai dalam konteks sekolah formal.

5. **Strategi penilaian belajar selain tutor formatif**  
   Dokumen sumber dengan sengaja menghindari kuis interaktif tradisional karena berpotensi menambah beban kognitif dan hambatan aksesibilitas. Namun, dokumen juga belum memberi rancangan alternatif penilaian yang sistematis selain dukungan tutor formatif. Belum dijelaskan bentuk asesmen sumatif, latihan tersruktur non-kuis, rubrik pemahaman konsep, pelaporan progres belajar, indikator ketercapaian kompetensi, maupun bagaimana guru menilai pemahaman siswa dari interaksi yang terjadi. Dengan kata lain, kerangka evaluasi belajar masih belum lengkap.

6. **Matriks kompatibilitas browser dan OS yang lengkap**  
   Kedua dokumen menekankan penggunaan screen reader native dan kepatuhan terhadap WCAG 2.2 AA, tetapi tidak menyajikan matriks kompatibilitas yang eksplisit. Belum ada daftar browser minimum, versi sistem operasi yang didukung, kombinasi browser-screen reader yang diuji, perilaku pada desktop vs mobile, maupun prioritas dukungan untuk NVDA, JAWS, VoiceOver, dan TalkBack dalam skenario nyata. Tanpa matriks ini, ruang lingkup QA aksesibilitas dan definisi "supported environment" masih belum cukup tegas.

Secara praktis, keenam area di atas sebaiknya diperlakukan sebagai **lampiran spesifikasi lanjutan** atau **dokumen turunan implementasi**, karena dokumen sumber saat ini belum menyediakan detail yang memadai untuk keputusan rekayasa, kebijakan operasional, dan pengujian produksi.

---

## 23. Format Ringkas untuk Dipahami AI

### 23.1 Product in one paragraph
InklusifMath adalah platform web aksesibel untuk pembelajaran matematika siswa tunanetra dan low vision. Guru mengunggah materi DOCX atau PDF teks digital, sistem mengekstrak struktur dan notasi matematika, AI menghasilkan narasi verbal baku untuk rumus, guru memverifikasi hasil, lalu modul dipublikasikan sebagai halaman HTML semantik yang dibaca screen reader native. Saat siswa butuh bantuan, mereka membuka tutor dengan `Alt + T`, bertanya lewat push-to-talk, dan menerima jawaban singkat kontekstual yang dibacakan screen reader tanpa kehilangan posisi fokus baca.

### 23.2 Core rules for AI systems
- Jangan gunakan audio naratif internal untuk membacakan materi.
- Semua bantuan harus kompatibel dengan screen reader native.
- Semua rumus harus punya representasi verbal yang tidak ambigu.
- Output clarifier harus selalu bisa diverifikasi dan diedit guru.
- Tutor harus singkat, kontekstual, dan menjaga fokus pengguna.
- Hindari pola interaksi yang meningkatkan beban kognitif.

### 23.3 Scope guardrails
- Hanya matematika dasar sampai pengantar aljabar.
- Hanya DOCX dan PDF teks digital.
- Tidak ada kuis interaktif tradisional.
- Tidak ada scan bitmap.
- Tidak ada TTS materi berbasis browser.

---

## 24. Kesimpulan

PRD ini merangkum dua dokumen sumber menjadi bentuk yang lebih eksplisit, terstruktur, dan mudah dipakai AI maupun tim produk. Fokus utamanya tetap sama: menghadirkan pembelajaran matematika yang aksesibel, semantik, dan bebas audio collision untuk siswa tunanetra dan low vision, dengan guru sebagai validator akhir dan AI sebagai alat bantu pra-pemrosesan serta bimbingan kontekstual.
