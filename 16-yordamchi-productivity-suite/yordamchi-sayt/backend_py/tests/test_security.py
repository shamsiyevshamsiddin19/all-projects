"""Ruxsat tekshiruvi va xavfsizlik jurnali testlari.

NIMA UCHUN AYNAN BU TESTLAR BIRINCHI YOZILDI
============================================
Backend 5 537 qator edi va unda bitta ham test yo'q edi. Birinchi testlar
eng ko'p zarar yetkaza oladigan joyga yozildi — ruxsat tekshiruviga.

Bu yerda qulflangan ikki haqiqiy voqea bor:

1. 2026-09-08 — serverda admin bo'lmagan faol foydalanuvchi quiz bazalarini
   va lug'at kategoriyalarini API orqali O'CHIRA OLARDI. Sabab: yozuv
   amallarida rol tekshirilmasdi, faqat "tizimga kirganmi" tekshirilardi.
   `test_oddiy_foydalanuvchi_admin_amalini_bajara_olmaydi` aynan shuni qoplaydi.

2. `_require_admin` beshta handler'da qo'lda ko'chirilgan edi. Bunday holatda
   mantiqni bir joyda tuzatib, qolgan to'rttasini unutish — eng tabiiy xato.
   `test_admin_tekshiruvi_faqat_bitta_joyda` buni STATIK ravishda taqiqlaydi:
   biror handler o'ziga yana nusxa yozsa, test darhol yiqiladi.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from app import security
from app.errors import ApiError
from conftest import make_request


# --- is_admin: kim admin hisoblanadi --------------------------------------

def test_allowed_emails_dagi_email_admin(admin_request):
    assert security.is_admin(admin_request) is True


def test_role_admin_sessiyasi_admin(user_request):
    """Kirish kodi orqali kirganda sessiyaga `role="admin"` qo'yiladi."""
    user_request.session["role"] = "admin"
    assert security.is_admin(user_request) is True


def test_oddiy_foydalanuvchi_admin_emas(user_request):
    assert security.is_admin(user_request) is False


def test_kirmagan_odam_admin_emas(anon_request):
    assert security.is_admin(anon_request) is False


@pytest.mark.parametrize("email", [
    "ADMIN@example.com",      # katta harf
    "  admin@example.com  ",  # bo'sh joy
    "Admin@Example.com",      # aralash
])
def test_email_registr_va_boshoq_joyga_sezgir_emas(email):
    """Sessiyadagi email turli ko'rinishda kelsa ham admin aniqlanishi kerak."""
    req = make_request({"doktor_id": 1, "doktor_email": email})
    assert security.is_admin(req) is True


def test_boshqa_email_admin_emas():
    """Admin emailiga o'xshash, lekin boshqa email — admin EMAS."""
    for email in ["admin@example.com.evil.uz", "xadmin@example.com", "admin@exampl.com"]:
        req = make_request({"doktor_id": 2, "doktor_email": email})
        assert security.is_admin(req) is False, email


# --- require_admin: 403 va JURNAL -----------------------------------------

def test_admin_otadi(admin_request):
    """Admin uchun hech qanday xato chiqmaydi."""
    security.require_admin(admin_request)  # xato bo'lmasligi kerak


def test_oddiy_foydalanuvchi_admin_amalini_bajara_olmaydi(user_request):
    """2026-09-08 dagi teshikning regressiya testi."""
    with pytest.raises(ApiError) as exc:
        security.require_admin(user_request)
    assert exc.value.status == 403


def test_kirmagan_odam_403_oladi(anon_request):
    with pytest.raises(ApiError) as exc:
        security.require_admin(anon_request)
    assert exc.value.status == 403


def test_xabar_moslashtirilishi_mumkin(user_request):
    with pytest.raises(ApiError) as exc:
        security.require_admin(user_request, "Boshqa xabar.")
    assert exc.value.message == "Boshqa xabar."


def test_rad_etish_jurnalga_yoziladi(user_request, caplog):
    """A-08: 403 faqat foydalanuvchiga qaytmasligi, izi ham qolishi kerak."""
    with caplog.at_level(logging.WARNING, logger="yordamchi.security"):
        with pytest.raises(ApiError):
            security.require_admin(user_request)

    yozuvlar = [r for r in caplog.records if r.name == "yordamchi.security"]
    assert len(yozuvlar) == 1, "rad etish aynan bir marta yozilishi kerak"

    matn = yozuvlar[0].getMessage()
    assert "UNAUTHORIZED_ADMIN" in matn
    assert "oddiy@example.com" in matn, "kim uringanini bilish shart"
    assert "203.0.113.9" in matn, "qayerdan uringanini bilish shart"
    assert "delete_db" in matn, "nimaga uringanini bilish shart"


def test_muvaffaqiyatli_ruxsat_jurnalni_toldirmaydi(admin_request, caplog):
    """Admin o'tganda yozuv bo'lmasin — aks holda jurnal shovqinga ko'miladi."""
    with caplog.at_level(logging.WARNING, logger="yordamchi.security"):
        security.require_admin(admin_request)
    assert [r for r in caplog.records if r.name == "yordamchi.security"] == []


# --- require_write_access -------------------------------------------------

def test_kirmagan_odam_401(anon_request, caplog):
    with caplog.at_level(logging.WARNING, logger="yordamchi.security"):
        with pytest.raises(ApiError) as exc:
            security.require_write_access(anon_request)
    assert exc.value.status == 401
    assert any("UNAUTHENTICATED" in r.getMessage()
               for r in caplog.records if r.name == "yordamchi.security")


def test_kirgan_odam_otadi(user_request):
    """Oddiy foydalanuvchi ham o'qish/yozishga kiradi — admin bo'lishi shart emas."""
    security.require_write_access(user_request)


# --- client_ip: nginx proxy ortida ----------------------------------------

def test_xff_sarlavhasi_ustun():
    """nginx ortida `request.client` — localhost. Haqiqiy IP X-Forwarded-For da."""
    req = make_request({}, headers={"X-Forwarded-For": "198.51.100.7, 10.0.0.1"},
                       client_host="127.0.0.1")
    assert security.client_ip(req) == "198.51.100.7"


def test_xff_bolmasa_client_host():
    req = make_request({}, client_host="198.51.100.9")
    assert security.client_ip(req) == "198.51.100.9"


def test_xff_bosh_bolsa_client_host():
    req = make_request({}, headers={"X-Forwarded-For": "   "}, client_host="198.51.100.9")
    assert security.client_ip(req) == "198.51.100.9"


# --- ARXITEKTURA TESTI: nusxa qaytib kelmasin -----------------------------

HANDLERS_DIR = Path(__file__).resolve().parent.parent / "app" / "handlers"


def test_admin_tekshiruvi_faqat_bitta_joyda():
    """A-07 regressiyasi: handler o'ziga admin tekshiruvini qayta yozmasin.

    Mezon — `role == "admin"` va `ALLOWED_EMAILS` ni BIRGA ishlatuvchi qator.
    Bu aynan ko'chirilgan nusxalarning imzosi edi. Ruxsat mantig'i faqat
    `security.is_admin()` da bo'lishi kerak.

    Istisno YO'Q: yangi handler ham shu qoidaga bo'ysunadi.
    """
    buzgan: list[str] = []
    for path in sorted(HANDLERS_DIR.glob("*.py")):
        matn = path.read_text(encoding="utf-8")
        for nomer, qator in enumerate(matn.splitlines(), 1):
            if 'role == "admin"' in qator and "ALLOWED_EMAILS" in qator:
                buzgan.append(f"{path.name}:{nomer}")

    assert buzgan == [], (
        "Admin tekshiruvi ko'chirilgan — `security.require_admin()` ishlatilsin: "
        + ", ".join(buzgan)
    )
