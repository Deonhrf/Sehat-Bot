# db.py
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='sehatbot_db'
    )

def get_user_by_email(email):
    db = get_db()
    cursor = db.cursor(dictionary=True) # <--- PENTING: biar bisa user['password']
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()

def create_user(name, email, password_hash):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password_hash))
        db.commit()
    finally:
        cursor.close()
        db.close()

def save_chat(user_id, role, message):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO chat_history (user_id, role, message) VALUES (%s, %s, %s)", (user_id, role, message))
        db.commit()
    finally:
        cursor.close()
        db.close()

def get_chat_history(user_id, limit=10):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT role, message as content FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s", (user_id, limit))
        history = cursor.fetchall()
        return history[::-1]
    finally:
        cursor.close()
        db.close()


def add_reminder_to_db(user_id, task, remind_at) :
    conn = get_db()
    if conn :
        cursor = conn.cursor()
        sql = "insert into reminders(user_id, task, remind_at) values (%s, %s, %s)"
        cursor.execute(sql,(user_id, task, remind_at))
        conn.commit() # save ke db
        cursor.close()
        conn.close()
        return True
    return False
