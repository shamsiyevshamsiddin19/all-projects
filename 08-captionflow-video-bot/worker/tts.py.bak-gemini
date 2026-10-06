"""Matnni ovozga aylantirish (TTS) — Gemini native audio, faqat rus/ingliz.

Nega faqat ru/en: Gemini TTS ko'p tilni "tushunadi", lekin o'zbek tilida
talaffuzi notabiiy chiqadi (aksent, urg'u xato) — shuning uchun sifat
kafolatlanadigan ikki tilga cheklaymiz (xuddi worker/correct.py da
CORRECT_LANGS bilan aksincha cheklangani kabi).

Oqim: Gemini xom PCM (16-bit, 24kHz, mono) qaytaradi -> vaqtinchalik .wav
qilib yoziladi -> ffmpeg orqali OGG/Opus'ga o'giriladi (Telegram ovozli
xabar shu formatni talab qiladi) -> yakuniy fayl yo'li qaytariladi.
"""
from __future__ import annotations

import logging
import os
import subprocess
import uuid
import wave

from config import settings

logger = logging.getLogger(__name__)

_MODEL = "gemini-2.5-flash-preview-tts"
_SAMPLE_RATE = 24000
MAX_CHARS = 5000

# Kunlik so'rov limiti (Google bepul tarif: gemini-2.5-flash-preview-tts uchun
# BUTUN LOYIHAGA 10 ta/kun — juda tor). Xato matnida "RESOURCE_EXHAUSTED" yoki
# "429" bo'lsa shu sabab — foydalanuvchiga tushunarli xabar ko'rsatiladi.
class QuotaExceeded(RuntimeError):
    pass


# Til uchun mos ovoz. "Kore" ikkala tilda ham tabiiy chiqadi.
_LANG_CONF = {
    "ru": {"voice": "Kore", "name": "rus"},
    "en": {"voice": "Kore", "name": "ingliz"},
}

# TTS modeli aslida suhbat (dialog) modeli — matn xom holida buyruq yoki
# savolga o'xshab ketsa, o'qib berish o'rniga MATN bilan "javob berishga"
# urinadi (400: "Model tried to generate text"). system_instruction bilan
# oldini olish mumkin edi, lekin bu model uchun AUDIO rejimida
# system_instruction 500 (INTERNAL) xato beradi — shuning uchun instruksiyani
# TURLI so'rov qatoriga emas, xuddi shu foydalanuvchi xabariga ichki qo'shamiz
# (Google'ning "Say cheerfully: ..." uslubiy ko'rsatma naqshi — model buni
# talaffuz qilmaydi, faqat ohang/qat'iylik ko'rsatmasi sifatida oladi).
_PREFIX = "Say exactly, without adding or answering anything: "


def _synthesize_pcm(text: str, lang: str) -> bytes:
    """Gemini orqali xom PCM audio (16-bit LE, mono, 24kHz) qaytaradi."""
    from google import genai
    from google.genai import errors, types

    from worker import usage
    usage.bump("gemini")
    usage.bump("gemini_tts")

    conf = _LANG_CONF[lang]
    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        resp = client.models.generate_content(
            model=_MODEL,
            contents=_PREFIX + text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=conf["voice"]
                        )
                    ),
                ),
            ),
        )
    except errors.ClientError as exc:
        msg = str(exc)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            raise QuotaExceeded("Kunlik TTS limiti tugadi") from exc
        raise

    parts = resp.candidates[0].content.parts
    for part in parts:
        data = getattr(part, "inline_data", None)
        if data and data.data:
            return data.data
    raise ValueError("Gemini TTS audio qaytarmadi")


def _pcm_to_wav(pcm: bytes, wav_path: str) -> None:
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16-bit
        w.setframerate(_SAMPLE_RATE)
        w.writeframes(pcm)


def _wav_to_ogg(wav_path: str, ogg_path: str) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-c:a", "libopus",
        "-b:a", "32k",
        "-vbr", "on",
        ogg_path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "ignore").strip()[-500:]
        raise RuntimeError(f"ffmpeg (tts) xato: {err}")
    if not os.path.exists(ogg_path):
        raise RuntimeError("OGG fayl yaratilmadi")


def text_to_voice(text: str, lang: str, work_dir: str | None = None) -> str:
    """Matnni ovozli xabar (.ogg/Opus) qiladi, fayl yo'lini qaytaradi.

    lang: "ru" yoki "en" (boshqasi ValueError). Chaqiruvchi asyncio.to_thread
    ichida ishlatishi kerak (sinxron: tarmoq + ffmpeg subprocess).
    """
    if lang not in _LANG_CONF:
        raise ValueError(f"TTS faqat ru/en uchun ishlaydi, berilgan: {lang}")
    text = (text or "").strip()
    if not text:
        raise ValueError("Matn bo'sh")
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]

    work_dir = work_dir or settings.work_dir
    os.makedirs(work_dir, exist_ok=True)
    job_id = uuid.uuid4().hex[:12]
    wav_path = os.path.join(work_dir, f"tts_{job_id}.wav")
    ogg_path = os.path.join(work_dir, f"tts_{job_id}.ogg")

    try:
        pcm = _synthesize_pcm(text, lang)
        _pcm_to_wav(pcm, wav_path)
        _wav_to_ogg(wav_path, ogg_path)
        return ogg_path
    finally:
        try:
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except OSError:
            pass
