"""Xavfsizlik sozlamalarining STANDART qiymatlari fail-closed bo'lishi.

NIMA UCHUN BU TEST BOR
======================
`REQUIRE_AUTH` standarti `False` edi va izohda "bu ilova login talab
qilmaydi" deb yozilgan edi. Sayt esa 2026-08-29 da Google bilan
qulflangan — ya'ni izoh eskirgan, standart esa xavfli qolgan.

Jonli saytda xavf yo'q edi, chunki `.env` da `REQUIRE_AUTH=true` turardi.
Xavf YASHIRIN edi: `.env` yo'qolsa, bo'sh fayl bilan almashsa yoki yangi
serverga ko'chirishda unutilsa — butun sayt (o'qish ham) hammaga ochilardi.

Standart qiymat — bu "hamma narsa yo'qolganda nima bo'ladi" degan savolga
javob. Shuning uchun u kodda qulflanadi, izohga ishonilmaydi.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def muhitsiz_config(monkeypatch):
    """`app.config` ni xavfsizlik o'zgaruvchilari BO'LMAGAN holda qayta yuklaydi.

    `Settings` atributlari modul import qilinganda hisoblanadi, shuning uchun
    standartni ko'rish uchun modulni qayta yuklash kerak. Oxirida asl holat
    tiklanadi, aks holda keyingi testlar buzilgan sozlama bilan ishlaydi.
    """
    import app.config as config

    for nom in ("REQUIRE_AUTH", "AUTH_MODE"):
        monkeypatch.delenv(nom, raising=False)
    # `load_dotenv` haqiqiy `.env` ni o'qib, standartni yashirib qo'ymasin.
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None, raising=False)

    yangi = importlib.reload(config)
    try:
        yield yangi.Settings()
    finally:
        # Asl muhitni qaytarib, modulni yana yuklaymiz.
        monkeypatch.undo()
        importlib.reload(config)


def test_require_auth_standarti_yoqilgan(muhitsiz_config):
    """Hech narsa sozlanmasa — sayt YOPIQ bo'lishi kerak, ochiq emas."""
    assert muhitsiz_config.REQUIRE_AUTH is True, (
        "REQUIRE_AUTH standarti False bo'lsa, .env yo'qolganda butun sayt "
        "autentifikatsiyasiz ochilib qoladi"
    )


def test_auth_mode_standarti_google(muhitsiz_config):
    """`.env` yo'qolsa parol bilan kirish qaytib ochilmasligi kerak."""
    assert muhitsiz_config.AUTH_MODE == "google"


def test_allowed_emails_standarti_bosh_royxat(monkeypatch):
    """Bu allaqachon to'g'ri edi — qulflab qo'yamiz.

    Ro'yxat sozlanmasa bo'sh bo'ladi, bo'sh ro'yxatda esa `is_admin_email()`
    hech kimni admin deb tanimaydi. Ya'ni noto'g'ri sozlashda sayt ochilib
    qolmaydi, yopilib qoladi.
    """
    import app.config as config

    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None, raising=False)
    monkeypatch.delenv("ALLOWED_EMAILS", raising=False)

    yangi = importlib.reload(config)
    try:
        assert yangi.Settings().ALLOWED_EMAILS == []
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_debug_standarti_ochirilgan(muhitsiz_config):
    """DEBUG yoqilsa xato tafsiloti (SQL, sxema) javobga chiqadi."""
    assert muhitsiz_config.DEBUG is False


def test_session_https_only_standarti_yoqilgan(muhitsiz_config):
    """Sessiya cookie'si faqat HTTPS orqali yuborilsin."""
    assert muhitsiz_config.SESSION_HTTPS_ONLY is True


def test_sirsiz_ishga_tushmaydi(monkeypatch):
    """`SESSION_SECRET` bo'lmasa va DEBUG o'chiq bo'lsa — RuntimeError.

    Bu allaqachon to'g'ri yozilgan (fail-loud) va shuning uchun qulflanadi:
    imzolanmagan sessiya cookie'si bilan ishga tushish — sessiyani soxtalashtirish
    imkoniyati degani.
    """
    import app.config as config

    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None, raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.setenv("APP_DEBUG", "false")

    # `config.py` oxirida `settings = get_settings()` turadi, shuning uchun
    # xato aynan QAYTA YUKLASH paytida chiqadi — bu kutilgan xatti-harakat.
    try:
        with pytest.raises(RuntimeError, match="SESSION_SECRET"):
            importlib.reload(config)
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_env_bilan_ochirish_mumkin(monkeypatch):
    """Lokal ishlash uchun himoyani o'chirish YO'LI BOR — lekin aniq harakat bilan."""
    import app.config as config

    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None, raising=False)
    monkeypatch.setenv("REQUIRE_AUTH", "false")
    monkeypatch.setenv("AUTH_MODE", "password")

    yangi = importlib.reload(config)
    try:
        s = yangi.Settings()
        assert s.REQUIRE_AUTH is False
        assert s.AUTH_MODE == "password"
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_env_example_standart_bilan_mos():
    """`.env.example` production uchun namuna — u fail-open bo'lmasin.

    Yangi server sozlanayotganda aynan shu fayl ko'chiriladi. Unda
    `REQUIRE_AUTH=false` turgan bo'lsa — yangi sayt ochiq holda ko'tariladi.
    """
    from pathlib import Path

    yol = Path(__file__).resolve().parent.parent / ".env.example"
    matn = yol.read_text(encoding="utf-8")

    assert "REQUIRE_AUTH=true" in matn, ".env.example da REQUIRE_AUTH=true bo'lishi kerak"
    assert "REQUIRE_AUTH=false" not in matn
    assert "AUTH_MODE=google" in matn
    assert "\nAUTH_MODE=password" not in matn
