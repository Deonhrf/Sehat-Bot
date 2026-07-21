# ai.py
import os
import json
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import pytz
from db import add_reminder_to_db # PENTING: INI JANGAN LUPA

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

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

def normalize_ai_response(text, user_name):
    if not text:
        return f"Maaf {user_name}, saya belum memahami. Bisa dijelaskan lagi?"
    text = " ".join(text.split())
    if len(text) > 220:
        text = text[:220].rstrip() + "..."
    return f"{text} Ini bukan diagnosis medis. Konsultasi ke dokter ya, {user_name}."
import pytz

def parse_time_to_iso(text):
    """Fallback kalau AI ngasih tanggal ngaco. Langsung bikin WIB"""
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz)
    target = now + timedelta(days=1)
    target = target.replace(hour=8, minute=0, second=0, microsecond=0)
    return target.strftime("%Y-%m-%dT%H:%M:%S") # HAPUS Z nya

def get_ai_response(user_name, history, new_message, user_id):
    if client is None:
        return "Maaf, kunci API belum diatur."

    # DETEKSI MINTA REMINDER ATAU TIDAK
    kata_kunci_reminder = ["ingetin", "ingatkan", "reminder", "jam", "besok", "nanti", "pukul"]
    butuh_reminder = any(kata in new_message.lower() for kata in kata_kunci_reminder)

    # UPDATE NAMA
    if "nama saya" in new_message.lower():
        user_name = new_message.lower().split("nama saya")[-1].strip().title()

    now_wib = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M')

    system_prompt = f"""Kamu adalah Sehat-Bot. Sapa user dengan nama {user_name}. Jawab ramah, singkat max 2 kalimat.
Waktu sekarang: {now_wib} WIB.

ATURAN KERAS:
1. HANYA panggil function add_reminder JIKA user minta diingatkan DAN menyebut waktu.
2. Jika user curhat gejala seperti 'pusing', 'sakit', JANGAN panggil function.
3. Jika user sapa 'pagi', 'halo', JANGAN panggil function.
Setiap jawaban biasa diakhiri: Ini bukan diagnosis medis. Konsultasi ke dokter ya."""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": new_message})

    # TOOL_CHOICE DINAMIS
    tool_choice_param = {"type": "function", "function": {"name": "add_reminder"}} if butuh_reminder else "none"
    tools_param = tools if butuh_reminder else []

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=180,
        temperature=0.2,
        tools=tools_param,
        tool_choice=tool_choice_param
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        function_args = json.loads(tool_call.function.arguments)
        task = function_args.get('task')
        remind_at = function_args.get('remind_at')

        if not remind_at or "2024" in remind_at:
            remind_at = parse_time_to_iso(new_message)

        success = add_reminder_to_db(user_id, task, remind_at) # INI UDAH BISA KEPAKE
        if success:
            # KODE BARU YG BENER
            tz = pytz.timezone('Asia/Jakarta')
            dt = datetime.strptime(remind_at, "%Y-%m-%dT%H:%M:%S") # anggap ini udah WIB
            dt = tz.localize(dt) # kasih label WIB
            waktu_baca = dt.strftime("%d %b %H:%M") # langsung format, jangan di convert lagi
            return f"Siap {user_name}! Pengingat '{task}' sudah saya catat untuk {waktu_baca} WIB. Ini bukan diagnosis medis. Konsultasi ke dokter ya."
        else:
            return f"Maaf {user_name}, gagal menyimpan pengingatnya."

    return normalize_ai_response(response_message.content, user_name)