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


-----------------------------------


## ⚙️ Cara Install & Menjalankan


### 1. Clone & Masuk Folder
git clone https://github.com/username/sehat-bot.git
cd sehat-bot


### 2. Buat Virtual Environment
python -m venv venv

Windows
venv\Scripts\activate

Mac/Linux
source venv/bin/activate


### 3. Install Library
pip install -r requirements.txt



### 4. Setup Database MySQL
Login ke MySQL dan jalankan query ini:
CREATE DATABASE sehatbot;
USE sehatbot;

CREATE TABLE users (

    id INT AUTO_INCREMENT PRIMARY KEY, 
    
    name VARCHAR(100) NOT NULL, 
    
    email VARCHAR(100) UNIQUE NOT NULL, 
    
    password VARCHAR(255) NOT NULL
);


CREATE TABLE chat_history (

    id INT AUTO_INCREMENT PRIMARY KEY, 
    
    user_id INT NOT NULL, 
    
    role VARCHAR(20) NOT NULL, 
    
    message TEXT NOT NULL, 
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


### 5. Setup File .env
Buat file .env di root folder dan isi:
SECRET_KEY=ubah_jadi_kunci_rahasia_panjang_banget
GROQ_API_KEY=gsk_masukkan_kunci_groq_kamu_disini


### 6. Jalankan Aplikasi
python app.py




## 📁 Struktur Folder
sehat-bot/
├── app.py                 # Aplikasi utama Flask
├── requirements.txt       # Daftar package yang dibutuhkan
├── .env                   # Secret keys 
├── .gitignore
├── README.md
└── templates/
    ├── index.html         # Halaman depan / landing page
    ├── login.html         # Halaman masuk
    ├── register.html      # Halaman daftar
    └── chat.html          # Halaman chat utama



### ⚠️ Disclaimer Penting
Sehat-Bot adalah asisten informasi kesehatan umum. 
Ini BUKAN diagnosis medis. 
Jawaban dari AI hanya saran awal. Untuk keluhan serius, segera konsultasi ke dokter atau tenaga kesehatan profesional.
