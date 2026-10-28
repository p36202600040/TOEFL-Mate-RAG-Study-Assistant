"""
src/generator.py — Generasi jawaban melalui Groq API.

Hanya potongan teks hasil retrieval yang dikirim ke LLM.
Seluruh PDF TIDAK pernah dikirim.
"""
import time

from groq import Groq

import config
from src.prompts import build_system_prompt, build_generation_prompt


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
    used_model = model or config.GROQ_MODEL

    if not config.GROQ_API_KEY:
        return {
            "answer": "",
            "model": used_model,
            "latency_seconds": 0.0,
            "contexts_used": contexts,
            "error": "GROQ_API_KEY tidak dikonfigurasi di file .env",
        }

    try:
        client = get_groq_client()
    except Exception as e:
        return {
            "answer": "",
            "model": used_model,
            "latency_seconds": 0.0,
            "contexts_used": contexts,
            "error": str(e),
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

        return {
            "answer": answer,
            "model": used_model,
            "latency_seconds": round(elapsed, 3),
            "contexts_used": contexts,
            "error": None,
        }

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        # Jangan tampilkan API key di error message
        if config.GROQ_API_KEY and config.GROQ_API_KEY in error_msg:
            error_msg = error_msg.replace(config.GROQ_API_KEY, "[REDACTED]")

        return {
            "answer": "",
            "model": used_model,
            "latency_seconds": round(elapsed, 3),
            "contexts_used": contexts,
            "error": f"Groq API error: {error_msg}",
        }

