# Sehat-Bot 💊
Asisten Kesehatan Virtual Berbasis AI + Pengingat Obat

Sehat-Bot adalah aplikasi web Flask yang berfungsi sebagai asisten kesehatan pribadi. 
Bot bisa diajak chat tentang keluhan ringan, menyimpan riwayat chat di MySQL, dan ada fitur pengingat jadwal minum obat.

Dibuat dengan Python, Flask, MySQL, dan Groq Llama-3.1

## ✨ Fitur Utama

- **🔐 Autentikasi**: Register & Login aman dengan password hashing Werkzeug
- **🤖 Chat AI**: Chat dengan Sehat-Bot berbasis Groq `llama-3.1-8b-instant`
- **🧠 Memori**: Bot mengingat 10 chat terakhir per user dari database
- **🗄️ Database**: Semua chat, user, dan obat tersimpan di MySQL
- **📱 Responsif**: Bisa dibuka di HP dan Desktop
- **🔒 Aman**: Kunci API dan Secret disimpan di `.env` dan diabaikan oleh `.gitignore`

## 🛠️ Teknologi yang Digunakan

- **Backend**: Python 3.10+, Flask
- **AI**: Groq API - Llama-3.1-8b-instant
- **Database**: MySQL / MariaDB
- **Frontend**: HTML5, CSS3, JavaScript Vanilla
- **Auth**: Flask-Session, Werkzeug Security
- **Environment**: python-dotenv



### ⚠️ Disclaimer Penting
Sehat-Bot adalah asisten informasi kesehatan umum. 
Ini BUKAN diagnosis medis. 
Jawaban dari AI hanya saran awal. Untuk keluhan serius, segera konsultasi ke dokter atau tenaga kesehatan profesional.