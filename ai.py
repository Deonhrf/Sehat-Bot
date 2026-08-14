# ai.py
import os
import json
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import pytz
from db import add_reminder_to_db
import httpx # TAMBAH INI

load_dotenv()

# 1. KASIH TIMEOUT 30 DETIK BIAR GAK NGGANTUNG
client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=httpx.Client(timeout=30.0) # INI BARU
) if os.getenv("GROQ_API_KEY") else None

tools = [
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": "Buat pengingat untuk user. Hanya panggil ketika user meminta diingatkan di waktu spesifik.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Kegiatan yg diingatkan. Contoh: minum vitamin"},
                    "remind_at": {"type": "string", "format": "date-time", "description": "Waktu ISO 8601. Format WAJIB: YYYY-MM-DDTHH:mm:ssZ"}
                },
                "required": ["task", "remind_at"],
                "additionalProperties": False
            },
        },
    }
]

def clean_iso_time(dt_string):
    if not dt_string: return None
    return dt_string.replace('Z', '').split('.')[0]

def normalize_ai_response(text, user_name):
    if not text: return f"Maaf {user_name}, saya belum memahami. Bisa dijelaskan lagi?"
    text = " ".join(text.split())
    if len(text) > 500: text = text[:500].rstrip() + "..."
    return f"{text} Semangatt Yahhh {user_name} :)"

def parse_time_to_iso(text):
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz)
    target = now + timedelta(days=1)
    target = target.replace(hour=8, minute=0, second=0, microsecond=0)
    return target.strftime("%Y-%m-%dT%H:%M:%S")

def get_ai_response(new_message, history, user_name, pdf_context):
    if client is None:
        return "Maaf, kunci API belum diatur."

    from flask import session
    user_id = session.get('user_id')

    kata_kunci_reminder = ["ingetin", "ingatkan", "reminder", "jam", "besok", "nanti", "pukul"]
    butuh_reminder = any(kata in new_message.lower() for kata in kata_kunci_reminder)

    now_wib = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M')

    system_prompt = f"""Kamu adalah Sehat-Bot. Sapa user dengan nama {user_name}. Jawab ramah, singkat max 2 kalimat.
                        Waktu sekarang: {now_wib} WIB.

                        RIWAYAT CHAT TERAKHIR:
                        ---
                        {history}
                        ---

                        KONTEKS PDF DARI USER:
                        ---
                        {pdf_context}
                        ---

                        ATURAN KERAS:
                        1. PRIORITAS 1: Gunakan RIWAYAT CHAT untuk jawab pertanyaan tentang user.
                        2. PRIORITAS 2: Gunakan KONTEKS PDF HANYA untuk jawab pertanyaan tentang isi PDF.
                        3. JANGAN campur data user dengan data dari PDF.
                        4. HANYA panggil function add_reminder JIKA user minta diingatkan DAN menyebut waktu.
                        5. Jika user curhat gejala, JANGAN panggil function. Beri saran umum saja + akhiri dengan disclaimer.
                        Apabila pembahasan mengenai kesahatan yang dialami siuser, setiap jawaban biasa diakhiri: Ini bukan diagnosis medis. Konsultasi ke dokter ya."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": new_message})

    tool_choice_param = {"type": "function", "function": {"name": "add_reminder"}} if butuh_reminder else "none"
    tools_param = tools if butuh_reminder else []

    # 2. BUNGKUS PAKE TRY EXCEPT BIAR GAK CRASH
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=250,
            temperature=0.1,
            tools=tools_param,
            tool_choice=tool_choice_param
        )
        response_message = response.choices[0].message
    except Exception as e:
        print("ERROR GROQ:", e)
        return f"Maaf {user_name}, Sehat-Bot lagi lemot. Coba kirim ulang ya. Ini bukan diagnosis medis. Konsultasi ke dokter ya."

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        function_args = json.loads(tool_call.function.arguments)
        task = function_args.get('task')
        remind_at = function_args.get('remind_at')

        if not remind_at or "2024" in remind_at:
            remind_at = parse_time_to_iso(new_message)

        success = add_reminder_to_db(user_id, task, remind_at)
        if success:
            remind_at = clean_iso_time(remind_at)
            dt = datetime.strptime(remind_at, "%Y-%m-%dT%H:%M:%S")
            tz = pytz.timezone('Asia/Jakarta')
            dt = tz.localize(dt)
            waktu_baca = dt.strftime("%d %b %H:%M")
            return f"Siap {user_name}! Pengingat '{task}' sudah saya catat untuk {waktu_baca} WIB. Ini bukan diagnosis medis. Konsultasi ke dokter ya."
        else:
            return f"Maaf {user_name}, gagal menyimpan pengingatnya."
    return normalize_ai_response(response_message.content, user_name)