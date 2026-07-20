from flask import Flask, redirect, render_template, request, jsonify, session, url_for, flash
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone 
import os
from db import get_user_by_email, create_user, save_chat, get_chat_history
from ai import get_ai_response

load_dotenv()
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = os.getenv("key_session")
app.config["JSON_SORT_KEYS"] = False

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

    save_chat(user_id, "user", message)
    history = get_chat_history(user_id)
    ai_answer = get_ai_response(user_name, history, message, user_id)
    save_chat(user_id, "assistant", ai_answer)

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)