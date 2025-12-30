# Google Workspace Integration Setup Guide

Panduan ini menjelaskan cara mengaktifkan integrasi Google Workspace di A.S.P.A V1.

## 📋 Layanan yang Tersedia

| Layanan | Contoh Perintah Suara |
|---------|----------------------|
| **📅 Google Calendar** | "Aspa, jadwalkan meeting besok jam 10 pagi" |
| **📊 Google Sheets** | "Aspa, baca spreadsheet saya" |
| **📁 Google Drive** | "Aspa, upload file ini ke Drive" |
| **✉️ Gmail** | "Aspa, kirim email ke tim marketing" |
| **📝 Google Docs** | "Aspa, buat dokumen proposal baru" |
| **📋 Google Forms** | "Ada, buat form pendaftaran baru" |
| **📽️ Google Slides** | "Ada, buat presentasi project update" |

---

## 🔧 Langkah Setup

### Step 1: Buat Google Cloud Project

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Klik **"Select a project"** → **"New Project"**
3. Beri nama project (contoh: "ADA-V2-Integration")
4. Klik **"Create"**

### Step 2: Aktifkan APIs

Di Google Cloud Console, aktifkan API berikut:

1. Buka **APIs & Services** → **Library**
2. Cari dan aktifkan setiap API berikut:
   - **Google Calendar API**
   - **Google Sheets API**
   - **Google Drive API**
   - **Gmail API**
   - **Google Docs API**
   - **Google Forms API**
   - **Google Slides API**

### Step 3: Konfigurasi OAuth Consent Screen

1. Buka **APIs & Services** → **OAuth consent screen**
2. Pilih **External** → **Create**
3. Isi form:
   - **App name**: ASPA V1
   - **User support email**: Email Anda
   - **Developer contact information**: Email Anda
4. Klik **Save and Continue**
5. Di halaman **Scopes**, klik **Add or Remove Scopes**
6. Tambahkan scopes berikut:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/documents`
   - `https://www.googleapis.com/auth/forms.body`
   - `https://www.googleapis.com/auth/presentations`
7. Klik **Update** → **Save and Continue**
8. Di halaman **Test users**, tambahkan email Google Anda
9. Klik **Save and Continue** → **Back to Dashboard**

### Step 4: Buat OAuth Credentials

1. Buka **APIs & Services** → **Credentials**
2. Klik **+ Create Credentials** → **OAuth client ID**
3. Pilih **Application type**: **Desktop app**
4. Beri nama (contoh: "ASPA Desktop")
5. Klik **Create**
6. Klik **Download JSON**
7. Rename file yang didownload menjadi `credentials.json`
8. Pindahkan file ke folder `backend/`:
   ```
   ada_v2/
   └── backend/
       └── credentials.json  ← Taruh di sini!
   ```

### Step 5: Install Dependencies

```bash
# Aktifkan virtual environment
conda activate ada_v2

# Install dependencies baru
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

### Step 6: Autentikasi Pertama

Saat pertama kali menggunakan fitur Google Workspace:

1. Jalankan A.S.P.A V1
2. Katakan: **"Aspa, authenticate with Google"** atau minta bantuan terkait Google Workspace
3. Browser akan terbuka untuk login
4. Pilih akun Google Anda
5. Klik **"Continue"** (aplikasi belum diverifikasi - ini normal untuk development)
6. Klik **"Continue"** lagi untuk memberikan izin
7. Setelah sukses, kembali ke A.D.A

**Token akan disimpan di `backend/google_token.json`** sehingga Anda tidak perlu login lagi.

---

## 🎤 Contoh Perintah Suara


### Calendar
- "Aspa, apa jadwal saya hari ini?"
- "Aspa, jadwalkan meeting dengan Tim Design besok jam 2 siang"
- "Aspa, hapus meeting yang tadi saya buat"

### Sheets
- "Aspa, baca data dari spreadsheet inventory"
- "Aspa, tambahkan data penjualan hari ini ke spreadsheet"
- "Aspa, buat spreadsheet baru bernama Laporan Bulanan"

### Drive
- "Aspa, tampilkan file di Google Drive saya"
- "Aspa, upload file CAD ini ke Drive"
- "Aspa, buat folder baru bernama Projects 2024"

### Gmail
- "Aspa, cek email terbaru saya"
- "Aspa, kirim email ke bos@perusahaan.com dengan subjek Laporan Mingguan"
- "Aspa, baca email dari HR"

### Docs
- "Aspa, buat dokumen baru berjudul Proposal Proyek"
- "Aspa, baca dokumen meeting notes"
- "Aspa, tambahkan catatan ke dokumen tersebut"

### Forms
- "Aspa, buat google form baru berjudul Survey Pelanggan"

### Slides
- "Aspa, buat presentasi baru berjudul Q1 Review"

---

## ⚠️ Troubleshooting

### "credentials.json not found"
Pastikan Anda sudah mendownload OAuth credentials dan menaruhnya di folder `backend/`.

### "Token has been expired or revoked"
Hapus file `backend/google_token.json` dan autentikasi ulang.

### "Access Not Configured"
Pastikan semua API yang diperlukan sudah diaktifkan di Google Cloud Console.

### "This app isn't verified"
Ini normal untuk development. Klik **"Continue"** untuk melanjutkan.

---

## 🔒 Keamanan

- **credentials.json** dan **google_token.json** berisi data sensitif
- Jangan pernah commit file-file ini ke Git
- File sudah ditambahkan ke `.gitignore`
- Token hanya berlaku untuk akun yang melakukan autentikasi

---

## 📫 Support

Jika ada masalah, pastikan:
1. Semua API sudah diaktifkan
2. `credentials.json` ada di folder yang benar
3. Email Anda sudah ditambahkan sebagai test user
4. Anda sudah menjalankan autentikasi pertama
