# Yahoo Mail Integration Setup

Feature ini memungkinkan A.S.P.A untuk membaca dan mengirim email menggunakan akun Yahoo Mail Anda via protokol standar IMAP dan SMTP.

## ⚠️ Prasyarat Penting: App Password

Yahoo Mail **tidak mengizinkan** login menggunakan password biasa untuk aplikasi pihak ketiga demi keamanan. Anda **WAJIB** membuat "App Password".

### Cara Membuat App Password:

1.  Login ke akun Yahoo Mail Anda di browser.
2.  Buka **Account Info** (atau klik foto profil -> Account Info).
3.  Pilih tab **Security**.
4.  Cari bagian **"Generate and manage app passwords"**.
5.  Masukkan nama aplikasi, misal: `ASPA Desktop`.
6.  Klik **Generate password**.
7.  **Salin password 16 karakter** yang muncul (tanpa spasi). Ini adalah password yang akan Anda gunakan.

## ⚙️ Konfigurasi .env

Tambahkan kredensial berikut ke file `.env` di folder root project (`d:\ADA-v3\.env`):

```env
YAHOO_EMAIL=email_anda@yahoo.com
YAHOO_PASSWORD=password_aplikasi_16_karakter
```

> **Catatan:** Jangan gunakan password login Yahoo Anda yang biasa! Gunakan App Password yang baru saja digenerate.

## 📋 Contoh Perintah (Jika Voice Command Diaktifkan)

Jika integrasi ini dihubungkan dengan logic AI (via `ada.py` tools definition):

- "Aspa, cek email yahoo terbaru"
- "Aspa, kirim email yahoo ke [email] tentang [subjek] isinya [pesan]"

## 🛠️ Testing

A.S.P.A akan otomatis mencoba terhubung saat startup jika variabel `.env` sudah diisi. Cek console log backend untuk memastikan tidak ada error koneksi.
