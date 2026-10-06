# -*- coding: utf-8 -*-
"""
FastAPI darsligini (8 ta bo'lim, 22 ta dars + Maxsus mavzular) language_topics jadvaliga yuklash.
"""
import os
import sys

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

FASTAPI_LANG = 'lang_1785561208734'

CHAPTERS = [
    {
        "dir": "00-bob-kirish",
        "folder": "00. Kirish",
        "lessons": [
            ("0.1-fastapi-nima-nima-uchun-tanlanadi.md", "0.1. FastAPI nima va nima uchun tanlanadi"),
            ("0.2-muhitni-sozlash-ubuntu-uv.md", "0.2. Muhitni sozlash: Ubuntu'da FastAPI loyihasini boshlash (uv)"),
        ]
    },
    {
        "dir": "01-bob-asoslar",
        "folder": "01. Asoslar",
        "lessons": [
            ("1.1-birinchi-ilova-avtomatik-hujjatlar.md", "1.1. Birinchi FastAPI ilovasi va avtomatik hujjatlar"),
            ("1.2-path-query-parametrlar.md", "1.2. Path va Query parametrlar"),
            ("1.3-request-body-response-model.md", "1.3. Request Body va Response Model"),
        ]
    },
    {
        "dir": "02-bob-pydantic-validatsiya",
        "folder": "02. Pydantic va validatsiya",
        "lessons": [
            ("2.1-pydantic-chuqur-validatorlar.md", "2.1. Pydantic v2 chuqur: Field, validatorlar va ichma-ich modellar"),
            ("2.2-xatolarni-boshqarish-fayl-yuklash.md", "2.2. Xatolarni boshqarish, fayl yuklash va formalar"),
        ]
    },
    {
        "dir": "03-bob-routing-di",
        "folder": "03. Routing va Dependency Injection",
        "lessons": [
            ("3.1-apirouter-loyiha-tuzilmasi.md", "3.1. APIRouter bilan loyihani tashkil etish"),
            ("3.2-dependency-injection-depends.md", "3.2. Dependency Injection (Depends) asoslari"),
            ("3.3-middleware-cors.md", "3.3. Middleware va CORS"),
        ]
    },
    {
        "dir": "04-bob-malumotlar-bazasi",
        "folder": "04. Ma'lumotlar bazasi",
        "lessons": [
            ("4.1-sqlmodel-postgresql-asoslari.md", "4.1. SQLModel asoslari va PostgreSQL bilan ulanish"),
            ("4.2-crud-amaliyotlari.md", "4.2. CRUD amaliyotlari"),
            ("4.3-alembic-migratsiyalar.md", "4.3. Alembic bilan migratsiyalar"),
            ("4.4-async-database.md", "4.4. Asinxron ma'lumotlar bazasi (async SQLAlchemy + asyncpg)"),
        ]
    },
    {
        "dir": "05-bob-autentifikatsiya",
        "folder": "05. Autentifikatsiya va xavfsizlik",
        "lessons": [
            ("5.1-oauth2-parol-xeshlash-jwt.md", "5.1. OAuth2, parol xeshlash va JWT token"),
            ("5.2-role-based-ruxsatlar.md", "5.2. Ruxsatlarni boshqarish (Role-Based Access Control)"),
        ]
    },
    {
        "dir": "06-bob-ilgor-mavzular",
        "folder": "06. Ilg'or mavzular",
        "lessons": [
            ("6.1-background-tasks-websocket.md", "6.1. Background Tasks va WebSocket"),
            ("6.2-testing-pytest-httpx.md", "6.2. FastAPI'ni testlash: pytest va httpx"),
            ("6.3-lifespan-async-best-practices.md", "6.3. Lifespan events va asinxron dasturlash bo'yicha eng yaxshi amaliyotlar"),
        ]
    },
    {
        "dir": "07-bob-production-deploy",
        "folder": "07. Production va Deploy",
        "lessons": [
            ("7.1-docker-bilan-konteynerlashtirish.md", "7.1. FastAPI ilovasini Docker bilan konteynerlashtirish"),
            ("7.2-nginx-worker-production.md", "7.2. Production: Uvicorn worker'lari va Nginx"),
            ("7.3-cicd-github-actions-yakuniy-loyiha.md", "7.3. CI/CD bilan GitHub Actions va yakuniy real loyiha"),
        ]
    }
]

def main():
    base_dir = '/opt/yordamchi/Yordamchisayt/database/seeds/fastapi_darslik'
    if not os.path.exists(base_dir):
        base_dir = '/home/shamsiddin/Documents/shamsiyev/Dasturlash/FastAPI-Darslik'

    print(f"Baza: {FASTAPI_LANG} dagi eski mavzularni tozalash...")
    db.execute("DELETE FROM language_topics WHERE lang = :l", {"l": FASTAPI_LANG})

    # 1. Add "M. Maxsus mavzular"
    print("M. Maxsus mavzular qo'shilmoqda...")
    special_content = """# Maxsus mavzular

Ushbu bo'lim FastAPI web frameworki, asinxron API yaratish va microservice arxitekturasi bo'yicha maxsus, chuqurlashtirilgan va amaliy mavzular uchun ajratilgan.

Bu yerga o'zingizning shaxsiy yoki maxsus darslaringizni qo'shishingiz mumkin."""

    db.execute(
        """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
           VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
        {
            "l": FASTAPI_LANG,
            "f": "M. Maxsus mavzular",
            "n": "M. Maxsus mavzular haqida",
            "c": special_content,
            "so": 0,
            "ot": "global",
            "ok": "shared"
        }
    )

    total_inserted = 1
    sort_counter = 1

    for chap in CHAPTERS:
        folder_name = chap["folder"]
        chap_dir = os.path.join(base_dir, chap["dir"])
        print(f"\n📁 Bob: [{folder_name}] ({chap_dir})")

        for fn, display_title in chap["lessons"]:
            fp = os.path.join(chap_dir, fn)
            if not os.path.exists(fp):
                print(f"  ❌ Fayl topilmadi: {fp}")
                continue

            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()

            db.execute(
                """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
                   VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
                {
                    "l": FASTAPI_LANG,
                    "f": folder_name,
                    "n": display_title,
                    "c": content,
                    "so": sort_counter,
                    "ot": "global",
                    "ok": "shared"
                }
            )
            print(f"  ✅ Yuklandi [{sort_counter}]: {display_title} ({len(content)} bayt)")
            sort_counter += 1
            total_inserted += 1

    print(f"\n🎉 Yakunlandi! Jami {total_inserted} ta FastAPI mavzusi bazaga muvaffaqiyatli yuklandi!")

if __name__ == '__main__':
    main()
