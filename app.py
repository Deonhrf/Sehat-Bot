from flask import Flask, redirect, render_template, request, jsonify, session, url_for, flash
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone 
import os
from db import get_user_by_email, create_user, save_chat, get_chat_history, save_pdf
from ai import get_ai_response
from rag import process_pdf_for_user
from werkzeug.utils import secure_filename # fungsi untuk membersihkan nama file 



load_dotenv()
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = os.getenv("key_session")
app.config["JSON_SORT_KEYS"] = False

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session: return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html", user_name=session.get("user_name"))



@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    user_id = session['user_id']
    user_name = session['user_name']

    if not message: return jsonify({"error": "Pesan kosong"}), 400

    save_chat(user_id, "user", message) # 1. Simpen dulu

    history = get_chat_history(user_id, 10) # 2. Ambil history

    from rag import search_user_docs # 3. Cari di PDF
    pdf_context = search_user_docs(message, user_id)

    ai_answer = get_ai_response(message, history, user_name, pdf_context) # 4. Kirim ke AI
    
    save_chat(user_id, "assistant", ai_answer) # 5. Simpen jawaban

    return jsonify({"ai_answer": ai_answer, "timestamp": datetime.now(timezone.utc).isoformat()})



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = get_user_by_email(request.form.get("email"))
        if user and bcrypt.check_password_hash(user['password'], request.form.get("password")): # <--- udah gak user[3]
            session["user_id"] = user['id']
            session["user_name"] = user['name']
            return redirect(url_for("chat"))
        flash("Email atau password salah", "error")
    return render_template("login.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name, email, password = request.form.get("name"), request.form.get("email"), request.form.get("password")
        if not name or not email or not password: flash("Semua data harus diisi", "danger")
        else:
            try:
                hash_pw = bcrypt.generate_password_hash(password).decode('utf-8')
                create_user(name, email, hash_pw)
                flash("Akun berhasil dibuat! Silakan login.", "success")
                return redirect(url_for("login"))
            except mysql.connector.IntegrityError: flash("Email sudah terdaftar", "danger")
    return render_template("register.html")


# pdf
@app.route('/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
    pdf = request.files['file'] # ambil pdf dari form
    filename = secure_filename(pdf.filename) # membersihakan nama file
    user_id = session['user_id']

    user_upload_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f"User_{user_id}")
    os.makedirs(user_upload_pdf, exist_ok=True)
    pdf_path = os.path.join(user_upload_pdf, filename)
    pdf.save(pdf_path) # menyimpan pdf kedalm folder


    # simpan ke db dulu
    save_pdf(user_id, filename, pdf_path)

    # cek isi filenya 
    if os.path.getsize(pdf_path) == 0:
        return jsonify({"status": "error", "message": "File PDF kosong atau gagal dibaca."}), 400

    # proses rag
    process_pdf_for_user(pdf_path, user_id)


    file_url = url_for('static', filename = f'uploads/User_{user_id}/{filename}')

    return jsonify({"status" : "sukses",
                    "filename" : filename,
                    "file_url" : file_url})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)