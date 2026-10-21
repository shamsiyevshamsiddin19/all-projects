# -*- coding: utf-8 -*-
"""
Foldex Xavfsizlik va Autentifikatsiya moduli.
Ushbu modul:
1. Telegram WebApp initData ni rasmiy HMAC-SHA256 algoritmi orqali tekshirish;
2. Telegram Login Widget ma'lumotlarini tekshirish;
3. JWT sessiya tokenlarini yaratish va dekodlash;
4. Xavfsiz bir martalik kirish tokenlarini (One-time auth tokens) yaratish;
5. Fayl nomlarini path traversal (katalogdan chiqib ketish) xurujlaridan tozalash funksiyalarini bajaradi.
"""

import hashlib
import hmac
import json
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, unquote

from jose import JWTError, jwt
from app.core.config import settings

# 1. Telegram WebApp initData ni tekshirish
def verify_telegram_webapp_data(init_data_raw: str) -> Optional[Dict[str, Any]]:
    """
    Telegram Mini App (WebApp) orqali yuborilgan initData ni rasmiy Telegram
    kriptografik standarti bo'yicha tekshiradi.

    Parametrlar:
        init_data_raw (str): window.Telegram.WebApp.initData qatori.

    Qaytaradi:
        dict: Agar ma'lumotlar haqiqiy bo'lsa va foydalanuvchi TELEGRAM_ADMIN_ID
              bilan mos kelsa, foydalanuvchi ma'lumotlari lug'ati. Aks holda None.
    """
    try:
        # a) Qatorni kalit-qiymat juftliklariga ajratish
        parsed_data = dict(parse_qsl(init_data_raw, keep_blank_values=True))
        if "hash" not in parsed_data:
            return None

        received_hash = parsed_data.pop("hash")

        # b) auth_date eskirganligini tekshirish (replay attack himoyasi: 86400 soniya / 24 soat)
        auth_date = int(parsed_data.get("auth_date", 0))
        current_time = int(time.time())
        if current_time - auth_date > 86400:
            return None

        # c) Kalitlarni alifbo tartibida saralab, ma'lumotlar tekshiruv qatorini hosil qilish
        data_check_list = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_list)

        # d) Maxfiy kalitni 'WebAppData' doimiysi va BOT_TOKEN dan hosil qilish
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=settings.BOT_TOKEN.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        # e) Hisoblangan HMAC hash qiymatini tekshirish
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        # f) Foydalanuvchi ma'lumotlarini o'qish va qat'iy ADMIN_ID ni tekshirish
        user_json_str = parsed_data.get("user")
        if not user_json_str:
            return None

        user_data = json.loads(user_json_str)
        user_id = user_data.get("id")

        # Qat'iy cheklov: Faqat TELEGRAM_ADMIN_ID foydalanuvchisi qabul qilinadi
        if user_id != settings.TELEGRAM_ADMIN_ID:
            return None

        return user_data

    except Exception:
        return None


# 2. Telegram Login Widget ma'lumotlarini tekshirish
def verify_telegram_widget_data(data: Dict[str, Any]) -> bool:
    """
    Telegram rasmiy Login Widget orqali kelgan callback ma'lumotlarini tekshiradi.
    """
    try:
        check_data = data.copy()
        received_hash = check_data.pop("hash", None)
        if not received_hash:
            return False

        # Telegram widget algoritmi: secret_key = SHA256(bot_token)
        secret_key = hashlib.sha256(settings.BOT_TOKEN.encode("utf-8")).digest()
        data_check_list = [f"{k}={v}" for k, v in sorted(check_data.items())]
        data_check_string = "\n".join(data_check_list)

        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return False

        # Faqat admin ID tekshiruvi
        if int(check_data.get("id", 0)) != settings.TELEGRAM_ADMIN_ID:
            return False

        return True
    except Exception:
        return False


# 3. JWT Sessiya Tokenlarini boshqarish
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Xavfsiz JWT sessiya tokenini yaratadi.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT tokenni tekshiradi va dekodlangan payloadni qaytaradi.
    Agar token noto'g'ri yoki eskirgan bo'lsa None qaytaradi.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        # Token ichidagi foydalanuvchi ID faqat TELEGRAM_ADMIN_ID bo'lishi shart
        user_id = payload.get("sub")
        if not user_id or int(user_id) != settings.TELEGRAM_ADMIN_ID:
            return None
        return payload
    except JWTError:
        return None


# 4. Bir martalik xavfsiz token (Botdan /login buyrug'i orqali kirish uchun)
def generate_one_time_token() -> str:
    """Kriptografik jihatdan xavfsiz 48 belgili noyob token generatsiya qiladi."""
    return secrets.token_urlsafe(36)


# 5. Fayl nomlarini tozalash va xavfsiz holatga keltirish
def sanitize_filename(filename: str) -> str:
    """
    Fayl nomidan noqonuniy belgilarni, '..' (directory traversal)
    va xavfli yo'l ajratgichlarni olib tashlaydi.
    """
    # a) Bo'sh joylar va chekka belgilarni qirqish
    filename = filename.strip()
    # b) Windows va Unix katalog ajratgichlarini tozalash
    filename = filename.replace("\\", "/").split("/")[-1]
    # c) Xavfli belgilarni olib tashlash, faqat harflar, raqamlar, nuqta, chiziqcha va pastki chiziqqa ruxsat berish
    # UTF-8 belgilarga ham (kirill, o'zbek lotin) ruxsat beriladi
    cleaned = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*]', '_', filename)
    # Agar fayl nomi bo'sh qolsa yoki faqat nuqtalardan iborat bo'lsa
    if not cleaned or cleaned.replace(".", "") == "":
        cleaned = f"fayl_{int(time.time())}.bin"
    return cleaned
