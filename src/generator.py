"""
src/generator.py — Generasi jawaban melalui Groq API.

Hanya potongan teks hasil retrieval yang dikirim ke LLM.
Seluruh PDF TIDAK pernah dikirim.
"""
import time

from groq import Groq

import config
from src.prompts import build_system_prompt, build_generation_prompt


def safe_generation_error(error: Exception) -> str:
    """Petakan error tanpa mengembalikan pesan atau detail provider."""
    name = type(error).__name__.lower()
    status = getattr(error, "status_code", None)
    message = str(error).lower()
    if status == 429 or "ratelimit" in name or "rate_limit" in message or "rate limit" in message:
        return "Layanan generasi sedang mencapai batas permintaan. Coba lagi beberapa saat lagi."
    if status in (401, 403) or "authentication" in name or "permission" in name:
        return "Autentikasi layanan generasi gagal. Periksa konfigurasi kredensial."
    if "timeout" in name:
        return "Layanan generasi melebihi batas waktu. Coba lagi."
    if status == 404 or "notfound" in name:
        return "Model yang dikonfigurasi tidak tersedia. Periksa GROQ_MODEL di .env."
    return "Layanan generasi gagal memproses permintaan. Coba lagi atau periksa konfigurasi."


def get_groq_client() -> Groq:
    """Buat Groq client. Raise error jika API key tidak tersedia."""
    if not config.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY tidak ditemukan. "
            "Salin .env.example ke .env dan isi GROQ_API_KEY Anda. "
            "Dapatkan API key di https://console.groq.com/keys"
        )
    return Groq(api_key=config.GROQ_API_KEY)


def generate_answer(
    question: str,
    contexts: list[dict],
    chat_history: list[dict] | None = None,
    language: str = "Indonesia",
    style: str = "penjelasan bertahap",
    level: str = "menengah",
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    """
    Generate jawaban menggunakan Groq API.

    Returns:
        dict dengan keys:
        - answer: str
        - model: str
        - latency_seconds: float
        - contexts_used: list[dict]
        - error: str | None
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)
    import os

    active_api_key = os.getenv("GROQ_API_KEY", config.GROQ_API_KEY).strip()
    active_model = (model if model is not None else config.GROQ_MODEL).strip()
    used_model = active_model

    if not active_api_key:
        return {
            "answer": "",
            "model": used_model,
            "latency_seconds": 0.0,
            "contexts_used": contexts,
            "error": "GROQ_API_KEY tidak dikonfigurasi di file .env",
        }

    try:
        client = Groq(api_key=active_api_key)
    except Exception as e:
        return {
            "answer": "",
            "model": used_model,
            "latency_seconds": 0.0,
            "contexts_used": contexts,
            "error": safe_generation_error(e),
        }

    system_prompt = build_system_prompt(language, style, level)
    messages = build_generation_prompt(question, contexts, chat_history)

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    used_max_tokens = max_tokens or config.GROQ_MAX_TOKENS
    used_temperature = temperature if temperature is not None else config.GROQ_TEMPERATURE

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model=used_model,
            messages=full_messages,
            max_tokens=used_max_tokens,
            temperature=used_temperature,
        )
        elapsed = time.time() - start_time

        answer = response.choices[0].message.content
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("empty response")

        return {
            "answer": answer,
            "model": getattr(response, "model", None) or used_model,
            "latency_seconds": round(elapsed, 3),
            "contexts_used": contexts,
            "error": None,
        }

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "answer": "",
            "model": used_model,
            "latency_seconds": round(elapsed, 3),
            "contexts_used": contexts,
            "error": safe_generation_error(e),
        }
