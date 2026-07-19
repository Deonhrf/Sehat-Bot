# ai.py
import os
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

def normalize_ai_response(text, user_name):
    if not text:
        return "Maaf, saya belum memahami. Bisa dijelaskan lagi?"
    text = " ".join(text.split())
    if len(text) > 220:
        text = text[:220].rstrip() + "..."
    return f"{text} Ini bukan diagnosis medis. Konsultasi ke dokter ya, {user_name}."

def get_ai_response(user_name, history, new_message):
    if client is None:
        return "Maaf, kunci API belum diatur."

    system_prompt = f"Kamu adalah Sehat-Bot. Sapa user dengan nama {user_name}. Jawab ramah, singkat, dan informatif. Selalu akhiri dengan disclaimer medis."

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": new_message})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=180,
        temperature=0.7,
    )
    return normalize_ai_response(response.choices[0].message.content, user_name)