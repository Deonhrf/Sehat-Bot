from flask import Flask, redirect, render_template, request, jsonify, session, url_for, flash
from dotenv import load_dotenv
from groq import Groq
import os
from datetime import datetime, timezone
import mysql
from flask_bcrypt import Bcrypt
import mysql.connector

app = Flask(__name__)
load_dotenv()
bcrypt = Bcrypt(app)
app.secret_key = os.getenv("key_session")

# koneski database
db = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = '',
    database = 'sehatbot_db'
)


app.config["JSON_SORT_KEYS"] = False

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


def normalize_ai_response(text):
    if not text:
        return "Maaf, saya belum memahami pertanyaan Anda. Bisa jelaskan keluhan Anda lebih singkat?"

    text = " ".join(text.split()).replace("\n", " ")
    text = text.replace("1.", "").replace("2.", "").replace("3.", "")

    if len(text) > 220:
        text = text[:220].rstrip() + "..."

    if "ini bukan diagnosis medis" not in text.lower():
        text = f"{text} Ini bukan diagnosis medis. Konsultasi ke dokter ya."

    return text


@app.route("/")
def index():
    return render_template("index.html")


    # fungsi untuk menyimpan chat kedalam db
def save_chat(user_id, role, message):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO chat_history (user_id, role, message)
        VALUES (%s, %s, %s)
    """, (user_id, role, message))
    db.commit()
    cursor.close()

def get_chat_history(user_id, limit=10) :
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        select role, message as content from chat_history where user_id = %s 
        order by timestamp DESC LIMIT %s
        """, (user_id, limit))
    history = cursor.fetchall()
    cursor.close()

    return history[::-1]


@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    return render_template("chat.html", 
                           user_name = session.get("user_name", "Teman") )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user_id" not in session: # <--- PROTEKSI
        return jsonify({"error": "Silakan login dulu"}), 401

    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        user_id = session['user_id']

        if not message:
            return jsonify({"error": "Pesan tidak boleh kosong"}), 400

        # 2. SIMPAN PESAN USER DULU
        save_chat(user_id, "user", message)

        # 3. AMBIL RIWAYAT CHAT
        history = get_chat_history(user_id)

        # 4. BIKIN PESAN BUAT GROQ
        messages_for_ai = [
            {
                "role": "system",
                "content": f"Kamu adalah Sehat-Bot. Sapa user dengan nama {session.get('user_name')}. Balas singkat max 2 kalimat, ramah. Akhiri dengan: 'Ini bukan diagnosis medis. Konsultasi ke dokter ya.'"
            }
        ]
        messages_for_ai.extend(history) # <--- MASUKIN MEMORY
        messages_for_ai.append({"role": "user", "content": message})

        if client is None:
            return jsonify({
                "ai_answer": "Maaf, kunci API belum diatur. Tambahkan GROQ_API_KEY di file.env",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages_for_ai, # <--- PAKE YG ADA MEMORY
            max_tokens=140,
            temperature=0.4,
        )

        ai_answer = response.choices[0].message.content
        ai_answer = normalize_ai_response(ai_answer)

        # 5. SIMPAN JAWABAN BOT
        save_chat(user_id, "assistant", ai_answer)

        return jsonify({
            "ai_answer": ai_answer,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({
            "ai_answer": "Maaf, saya sedang tidak bisa terhubung saat ini. Coba lagi sebentar lagi.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone() # ambil hasil data user dari database
        cursor.close()
        if user and bcrypt.check_password_hash(user[3], password):  
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            # flash(f"Selamat datang, {user[1]}! 🎉", "success")
            return redirect(url_for("chat"))  # simpan nama user ke session
        else:
            flash("Email atau password salah. Silakan coba lagi.", "error")
    return render_template("login.html")



@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST" :
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # validasi sederhan 
        if not name or not email or not password :
            flash("Semua data harus diisi", "danger")
            return redirect(url_for("register"))

        try:
            hash_pw = bcrypt.generate_password_hash(password).decode('utf-8')
            
            cursor = db.cursor()
            cursor.execute("""insert into users (name, email, password) values (%s, %s, %s)""", (name, email, hash_pw))
            db.commit()
            cursor.close()
            flash("Akun berhasil dibuat! Silakan login.", "success")
            return redirect(url_for("login"))

        except Exception as e :
            flash("Maaf sistem sedang sibuk", "danger")
            return redirect(url_for('register'))
        
    return render_template("register.html")



# run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)