# Leksikon Matematika Baku Bahasa Indonesia
## InklusifMath Platform
### Panduan Narasi Verbal untuk AI Semantic Clarifier dan Guru

---

## 1. Metadata Dokumen

- **Versi:** 1.0-draft
- **Status:** Draft — memerlukan validasi guru SLB-A / guru matematika inklusif
- **Tujuan:** Menjadi referensi baku bagi AI semantic clarifier (Gemini) dan guru reviewer untuk menghasilkan narasi verbal notasi matematika yang tidak ambigu saat dibacakan screen reader
- **Bahasa:** Indonesia
- **Cakupan:** Matematika dasar sampai pengantar aljabar (sesuai PRD Section 8.2)

---

## 2. Prinsip Narasi

1. **Tidak ambigu** — Narasi harus menghasilkan satu interpretasi tunggal. Hindari kata yang bisa merujuk ke operasi berbeda.
2. **Struktur eksplisit** — Sebutkan struktur (pembilang, penyebut, pangkat, akar) secara eksplisit, bukan hanya membaca simbol.
3. **Urutan baca natural** — Narasi dibaca dari kiri ke kanan sesuai urutan operasi, dengan sisipan struktur bila diperlukan.
4. **Bahasa Indonesia baku** — Gunakan istilah Kamus Besar Bahasa Indonesia dan buku teks matematika resmi.
5. **Singkat tapi lengkap** — Satu narasi per ekspresi, sependek mungkin tanpa mengorbankan kejelasan.

---

## 3. Leksikon Simbol Dasar

### 3.1 Operasi Aritmatika

| Simbol | Narasi Baku | ❌ Hindari | Contoh |
|--------|-------------|------------|--------|
| `+` | "ditambah" | "plus", "tambah" | `3 + 5` → "tiga ditambah lima" |
| `-` | "dikurangi" | "minus", "kurang" | `8 - 3` → "delapan dikurangi tiga" |
| `×` atau `·` | "dikali" | "kali", "times" | `4 × 7` → "empat dikali tujuh" |
| `÷` atau `/` (pembagian) | "dibagi" | "per" (ambigu dengan pecahan) | `12 ÷ 4` → "dua belas dibagi empat" |
| `=` | "sama dengan" | "adalah", "hasilnya" | `3 + 5 = 8` → "tiga ditambah lima sama dengan delapan" |
| `≠` | "tidak sama dengan" | "bukan" | `5 ≠ 3` → "lima tidak sama dengan tiga" |
| `≈` | "kira-kira sama dengan" | "hampir" | `π ≈ 3,14` → "pi kira-kira sama dengan tiga koma empat belas" |

### 3.2 Perbandingan

| Simbol | Narasi Baku | ❌ Hindari |
|--------|-------------|------------|
| `<` | "kurang dari" | "lebih kecil" |
| `>` | "lebih dari" | "lebih besar" |
| `≤` | "kurang dari atau sama dengan" | "kurang sama dengan" |
| `≥` | "lebih dari atau sama dengan" | "lebih sama dengan" |

### 3.3 Tanda Kurung dan Pengelompokan

| Simbol | Narasi Baku | Contoh |
|--------|-------------|--------|
| `( )` | "buka kurung ... tutup kurung" | `(3 + 5)` → "buka kurung tiga ditambah lima tutup kurung" |
| `[ ]` | "buka kurung siku ... tutup kurung siku" | |
| `{ }` | "buka kurung kurawal ... tutup kurung kurawal" | |

> **Alternatif untuk ekspresi sederhana:** Jika isi kurung singkat, boleh gunakan "kelompok" sebagai pengganti.
> Contoh: `2(x + 3)` → "dua dikali kelompok x ditambah tiga"

---

## 4. Leksikon Struktur Matematika

### 4.1 Pecahan

**Aturan:** Selalu sebutkan "pecahan", "pembilang", dan "penyebut" secara eksplisit.

| Notasi | Narasi Baku | ❌ Hindari |
|--------|-------------|------------|
| `½` | "satu per dua" atau "setengah" | "satu bagi dua" |
| `⅓` | "satu per tiga" atau "sepertiga" | |
| `¼` | "satu per empat" atau "seperempat" | |
| `¾` | "tiga per empat" | |
| `a/b` (umum) | "pecahan dengan pembilang a dan penyebut b" | "a per b" (ambigu dengan pembagian) |
| `2/3` | "pecahan dua per tiga" | "dua bagi tiga" |
| `(2x+1)/(x-3)` | "pecahan dengan pembilang dua x ditambah satu dan penyebut x dikurangi tiga" | |

**Kapan gunakan bentuk pendek vs panjang:**
- Pecahan sederhana (angka tunggal): boleh bentuk pendek → "dua per tiga"
- Pecahan dengan ekspresi di pembilang/penyebut: WAJIB bentuk panjang → "pecahan dengan pembilang ... dan penyebut ..."

### 4.2 Pangkat dan Eksponen

| Notasi | Narasi Baku | ❌ Hindari |
|--------|-------------|------------|
| `a²` | "a pangkat dua" atau "a kuadrat" | "a dua", "a squared" |
| `a³` | "a pangkat tiga" atau "a kubik" | "a tiga" |
| `aⁿ` | "a pangkat n" | |
| `2³` | "dua pangkat tiga" | "dua tiga" |
| `10²` | "sepuluh kuadrat" | |

### 4.3 Akar

| Notasi | Narasi Baku | ❌ Hindari |
|--------|-------------|------------|
| `√a` | "akar kuadrat dari a" | "akar a", "root a" |
| `√9` | "akar kuadrat dari sembilan" | |
| `³√a` | "akar pangkat tiga dari a" | "akar kubik a" |
| `√(x+1)` | "akar kuadrat dari kelompok x ditambah satu" | |

### 4.4 Nilai Mutlak

| Notasi | Narasi Baku | ❌ Hindari |
|--------|-------------|------------|
| `|a|` | "nilai mutlak dari a" | "absolut a" |
| `|-5|` | "nilai mutlak dari negatif lima" | |

### 4.5 Persentase dan Rasio

| Notasi | Narasi Baku | ❌ Hindari |
|--------|-------------|------------|
| `a%` | "a persen" | |
| `25%` | "dua puluh lima persen" | |
| `a : b` | "perbandingan a banding b" | "a titik dua b" |
| `2 : 3` | "perbandingan dua banding tiga" | |

---

## 5. Leksikon Aljabar Dasar

### 5.1 Variabel dan Koefisien

| Notasi | Narasi Baku | ❌ Hindari |
|--------|-------------|------------|
| `x` | "x" | |
| `2x` | "dua x" | "dua kali x" (boleh untuk kejelasan ekstra) |
| `-3x` | "negatif tiga x" | "minus tiga x" |
| `xy` | "x dikali y" | "xy" (tidak jelas saat dibaca) |

### 5.2 Persamaan Linear

| Notasi | Narasi Baku |
|--------|-------------|
| `x = 5` | "x sama dengan lima" |
| `3x + 2 = 11` | "tiga x ditambah dua sama dengan sebelas" |
| `2x - 7 = x + 3` | "dua x dikurangi tujuh sama dengan x ditambah tiga" |
| `x/4 = 3` | "x dibagi empat sama dengan tiga" |

### 5.3 Pertidaksamaan

| Notasi | Narasi Baku |
|--------|-------------|
| `x > 5` | "x lebih dari lima" |
| `2x + 1 ≤ 9` | "dua x ditambah satu kurang dari atau sama dengan sembilan" |

---

## 6. Leksikon Bilangan

### 6.1 Jenis Bilangan

| Notasi | Narasi Baku |
|--------|-------------|
| `-5` | "negatif lima" |
| `+3` | "positif tiga" |
| `0,75` | "nol koma tujuh lima" |
| `3,14` | "tiga koma satu empat" |

> **Aturan desimal:** Angka setelah koma dibaca per digit, bukan sebagai bilangan utuh.
> `0,25` → "nol koma dua lima" (bukan "nol koma dua puluh lima")

### 6.2 Konstanta Umum

| Simbol | Narasi Baku |
|--------|-------------|
| `π` | "pi" |
| `∞` | "tak hingga" |

---

## 7. Leksikon KPK dan FPB

| Istilah | Narasi Baku |
|---------|-------------|
| KPK | "KPK" atau "Kelipatan Persekutuan Terkecil" |
| FPB | "FPB" atau "Faktor Persekutuan Terbesar" |
| KPK(12, 8) = 24 | "KPK dari dua belas dan delapan sama dengan dua puluh empat" |
| FPB(12, 8) = 4 | "FPB dari dua belas dan delapan sama dengan empat" |

---

## 8. Aturan Komposisi Ekspresi Kompleks

Saat ekspresi terdiri dari beberapa bagian, gunakan aturan berikut:

### 8.1 Urutan pembacaan
Baca dari kiri ke kanan, dengan menyisipkan kata penghubung struktur.

### 8.2 Pemisahan bagian
Gunakan jeda natural (koma dalam narasi) untuk memisahkan term.

### 8.3 Contoh komposisi

| Ekspresi | Narasi Baku |
|----------|-------------|
| `2/3 + 1/4 = 11/12` | "pecahan dua per tiga, ditambah pecahan satu per empat, sama dengan pecahan sebelas per dua belas" |
| `(x + 2)² = x² + 4x + 4` | "kelompok x ditambah dua pangkat dua, sama dengan x kuadrat ditambah empat x ditambah empat" |
| `√(a² + b²)` | "akar kuadrat dari kelompok a kuadrat ditambah b kuadrat" |
| `3(2x - 5) + 7 = 4` | "tiga dikali kelompok dua x dikurangi lima, ditambah tujuh, sama dengan empat" |
| `x/2 + 3 = x/5 - 1` | "x dibagi dua ditambah tiga, sama dengan x dibagi lima dikurangi satu" |

---

## 9. Panduan untuk AI Prompt

System prompt berikut HARUS digunakan oleh AI Semantic Clarifier:

```
Kamu adalah ahli narasi matematika bahasa Indonesia untuk siswa tunanetra.

TUGAS:
Ubah notasi matematika menjadi narasi verbal yang tidak ambigu.

ATURAN WAJIB:
1. Gunakan leksikon baku InklusifMath (terlampir).
2. Untuk pecahan, SELALU sebutkan "pecahan" dan/atau "pembilang" dan "penyebut".
3. Untuk pangkat, SELALU katakan "pangkat" diikuti angka.
4. Untuk akar, SELALU katakan "akar kuadrat dari".
5. JANGAN gunakan kata "per" untuk operasi pembagian.
6. JANGAN gunakan istilah Inggris.
7. Angka desimal: baca per digit setelah koma.
8. Satu narasi per ekspresi, sependek mungkin tanpa mengorbankan kejelasan.
9. JANGAN gunakan kata visual seperti "lihat", "perhatikan gambar".

FORMAT OUTPUT:
- Hanya teks narasi, tanpa simbol matematika.
- Satu kalimat per ekspresi.
```

---

## 10. Catatan Validasi

> **PENTING:** Leksikon ini adalah draft awal yang disusun berdasarkan konvensi umum buku teks matematika bahasa Indonesia. Sebelum difinalisasi, leksikon HARUS divalidasi oleh:
>
> 1. Guru matematika SLB-A (Sekolah Luar Biasa bagian A — tunanetra)
> 2. Siswa tunanetra yang sudah terbiasa belajar matematika dengan screen reader
> 3. Ahli pendidikan matematika inklusif
>
> Validasi bertujuan memastikan bahwa istilah yang dipakai sesuai dengan konvensi yang sudah familiar bagi komunitas tunanetra di Indonesia.
