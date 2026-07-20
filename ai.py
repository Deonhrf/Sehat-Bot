# ai.py
import os
import json
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timezone
from db import add_reminder_to_db

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

tools = [
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": "Gunakan tool ini hanya jika user secara eksplisit meminta dibuatkan pengingat atau reminder di waktu tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Apa yang harus diingatkan. Contoh: minum vitamin"},
                    "remind_at": {"type": "string", "description": "Waktu pengingat dalam format YYYY-MM-DD HH:MM:SS"},
                },
                "required": ["task", "remind_at"],
            },
        },
    }
]


def normalize_ai_response(text, user_name):
    if not text:
        return "Maaf, saya belum memahami. Bisa dijelaskan lagi?"
    text = " ".join(text.split())
    if len(text) > 220:
        text = text[:220].rstrip() + "..."
    return f"{text} Ini bukan diagnosis medis. Konsultasi ke dokter ya, {user_name}."

def get_ai_response(user_name, history, new_message, user_id):
    if client is None:
        return "Maaf, kunci API belum diatur."

    system_prompt = f"Kamu adalah Sehat-Bot. Sapa user dengan nama {user_name}. Jawab ramah, singkat, dan informatif. Selalu akhiri dengan disclaimer medis. Jika user meminta pengingat atau reminder, gunakan tool 'add_reminder' dengan format yang benar. Jangan tambahkan penjelasan di luar tool call."

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": new_message})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=180,
        temperature=0.3,
        tools=tools,
        tool_choice="auto"
    )

    # ambil jawaban dari Ai
    response_message = response.choices[0].message

    if response_message.tool_calls :
        tool_call = response_message.tool_calls[0]
        function_name = tool_call.function.name # ambil nama fungsi yang diminta ai
        function_args = json.loads(tool_call.function.arguments) # ambil data yang diisi ai
        if function_name == "add_reminder":
            succes = add_reminder_to_db(user_id, 
                                        function_args.get('task'),
                                        function_args.get('remind_at'))
            if succes : 
                return f"Siap {user_name}! Pengingat '{function_args['task']}' sudah saya catat untuk jam {function_args['remind_at']}. Ini bukan diagnosis medis. Konsultasi ke dokter ya."
            else:
                return "Maaf gagal menyimpan pengingatnya."

    return normalize_ai_response(response.choices[0].message.content, user_name)

