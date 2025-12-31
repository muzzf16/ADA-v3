## Draft Rencana Pengembangan K.E.N.E.S (Markdown)

> Catatan: Ringkasan ini menggabungkan arsitektur, fitur MVP, fitur lanjutan, integrasi n8n, dan fokus use case pribadi + BPR, agar bisa jadi acuan kerja ke depan.[^1]

***

## 1. Tujuan Sistem

- Menjadikan K.E.N.E.S sebagai **asisten profesional pribadi** untuk email, meeting, dan tugas, yang ke depan bisa di-scale ke staf kantor lain.[^1]
- Menjadikan K.E.N.E.S sebagai **orchestrator workflow BPR**, dengan n8n sebagai eksekutor proses (rekonsiliasi, laporan, KPI, reminder compliance).[^1]

***

## 2. Arsitektur Tingkat Tinggi

### 2.1 Komponen Utama

- **Frontend (Electron + React)**
    - UI interaktif, gesture control, face authentication.[^1]
    - Komunikasi ke backend via Socket.IO.
- **Backend (Python + FastAPI)**
    - `server.py` sebagai gateway request.
    - `ada.py` / modul KENES sebagai otak (Gemini 2.5 Native Audio + reasoning).[^1]
    - Kumpulan **Agent**:
        - Web Agent (Playwright).
        - Google Workspace Agent (Gmail, Calendar, Drive, Docs, Sheets, Slides, Forms).
        - Local PC Agent (file, aplikasi, printer).
        - WhatsApp/Webhook Agent.
        - Printer Agent.
        - N8N Agent (untuk trigger workflow).[^1]
- **Lapis Keamanan \& Konfigurasi**
    - `settings.json` (face_auth_enabled, tool_permissions).[^1]
    - `.env` (API keys, kredensial).

***

## 3. Fitur MVP (Fase 1 – “Asisten Profesional Dasar”)

### 3.1 Voice \& Chat Interface

- Input via suara dan teks (aplikasi desktop, chat internal).
- Mode wake phrase atau push-to-talk untuk memulai sesi.


### 3.2 Email Assistant Dasar

- Ringkasan email harian (“ringkas email penting hari ini”).
- Triage ringan: menandai email penting/urgent.
- Draft reply (tidak langsung kirim; wajib review manual).


### 3.3 Calendar Assistant Dasar

- Menampilkan jadwal hari ini/minggu ini.
- Membuat event sederhana (judul, waktu, peserta).
- Deteksi konflik dan menawarkan alternatif waktu.


### 3.4 Task \& Reminder Dasar

- Membuat tugas dari perintah suara/teks.
- Menampilkan daftar tugas penting per hari/minggu.


### 3.5 Konfirmasi Aksi Kritis

- Selalu minta konfirmasi eksplisit untuk:
    - Kirim email ke pihak lain.
    - Menghapus/merubah event.
    - Aksi file yang sensitif (hapus/timpa).

***

## 4. Fitur Lanjutan (Fase 2–3 – “Asisten Profesional Cerdas”)

### 4.1 Orkestrasi \& Reasoning

- Task planner di backend untuk memecah perintah kompleks menjadi langkah kecil (cek email → susun agenda → buat meeting → kirim undangan).
- Routing intent → agent yang tepat (Gmail, Calendar, Local, Web, n8n) dengan guardrail dan fallback.


### 4.2 Daily Brief \& Meeting Intelligence

- **Daily Brief**
    - Ringkasan pagi/sore: email penting, agenda hari ini/besok, tugas jatuh tempo.
- **Meeting Pack**
    - Sebelum meeting: rangkum email dan dokumen terkait, susun draft agenda dan poin diskusi.
    - Setelah meeting (bila ada transkrip): ringkasan, keputusan, dan daftar action items → otomatis jadi tugas/blok waktu.


### 4.3 Auto Follow-Up \& Komitmen Terselip

- Deteksi komitmen dalam email/chat (janji follow-up, janji kirim laporan/dokumen).
- Otomatis membuat task atau blok waktu di kalender.


### 4.4 Personalization

- Profil user:
    - Bahasa, gaya email (formal/semiformal/santai).
    - Jam kerja, durasi default meeting.
    - Daftar klien/proyek penting.
- Asisten menyesuaikan gaya balasan dan prioritas berdasarkan profil ini.

***

## 5. Integrasi n8n untuk Workflow BPR \& Productivity

### 5.1 Pola Integrasi Umum

- n8n self-host sebagai “tangan eksekusi” untuk workflow.
- Webhook di n8n menjadi entry point (contoh path):
    - `/kenes/run/daily-brief`
    - `/kenes/run/recon-harian`
    - `/kenes/run/laporan-kpi`
- N8N Agent di KENES:
    - Hanya boleh memanggil domain n8n dengan path yang di-whitelist.
    - Mengirim JSON berisi `user_id`, `role`, `intent`, dan parameter bisnis (tanggal, cabang, dsb.).


### 5.2 Workflow Produktivitas

- **Daily Brief Workflow (n8n)**
    - Trigger: webhook dari KENES.
    - Aksi: ambil email \& event → rangkum → kembalikan JSON ke KENES.
- **Meeting Pack Workflow (n8n)**
    - Input: peserta, waktu, topik.
    - Aksi: cari email \& file terkait → susun konteks dan agenda → kirim ke KENES / email user.


### 5.3 Workflow Finance/BPR


- **Reminder \& Compliance**
    - n8n menjadwalkan pengecekan deadline laporan regulasi dan tugas penting.
    - Jika mendekati jatuh tempo, memicu notifikasi ke KENES untuk mengingatkan via voice/email.

***

## 6. Multi-user, Role, dan Keamanan

### 6.1 Role \& Tool Permissions

- Menetapkan role (misalnya: Personal, IT, Operasional, AO, Manajemen).
- Menghubungkan `tool_permissions` dengan role:
    - Batasan akses tool sensitif (web agent, write/delete file, eksekusi workflow tertentu).
    - Mode read-only vs write untuk workflow keuangan.


### 6.2 Approval Flow Aksi Sensitif

- Untuk tindakan seperti:
    - Kirim email penting ke eksternal (OJK/vendor).
    - Trigger workflow finansial besar.
    - Akses file rahasia.
- Pola: assistant menyiapkan draft → meminta konfirmasi (voice + klik / PIN) → log ke audit trail.


### 6.3 Konteks Terpisah Per Pengguna

- Menyimpan memori kerja dan preferensi per user: proyek aktif, klien penting, jadwal rutin, dll.
- Saat sistem di-scale, setiap staf mendapatkan asisten dengan konteksnya sendiri di atas backend yang sama.


### 6.4 Keamanan Integrasi n8n

- Proteksi endpoint n8n dengan autentikasi dan pembatasan akses jaringan.
- Penggunaan path webhook spesifik dan terpisah antara staging/test dan production.
- Backup rutin dan pemantauan resource n8n untuk menjamin ketersediaan.

***

## 7. Roadmap Implementasi (High-Level)

### Fase 1 – Personal Pro Assistant (1–2 bulan)

- Stabilkan integrasi Gmail/Calendar di KENES.
- Implementasi:
    - Daily brief dasar (tanpa n8n atau dengan n8n sederhana).
    - Draft email, jadwal meeting, task \& reminder dasar.
- Buat 1–2 workflow n8n awal untuk mendukung daily brief dan meeting pack sederhana.


### Fase 2 – Finance \& BPR Workflows (2–3 bulan)

- Tambah workflow n8n: rekonsiliasi harian, laporan KPI, dan reminder compliance.
- Integrasikan KENES untuk menyajikan hasil dan angka utama dengan bahasa natural.


### Fase 3 – Multi-user \& Governance

- Implementasi role, policy per tool, dan audit log detail.
- Menambahkan approval flow untuk aksi sensitif.
- Uji coba dengan beberapa user internal (staf BPR) dan refined UX + batasan keamanan.

***

Dengan dokumen ini, KENES bisa dikembangkan terstruktur: mulai dari asisten pribadi yang kuat, lalu pelan-pelan naik menjadi asisten profesional yang mengerti workflow BPR dan aman untuk dipakai oleh banyak staf.

<div align="center">⁂</div>

[^1]: https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/153302360/b832a329-1c29-4e30-bcd0-f1a6e59b6210/README.md

