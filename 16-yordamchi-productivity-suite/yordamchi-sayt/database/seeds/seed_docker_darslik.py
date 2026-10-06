# -*- coding: utf-8 -*-
"""
Docker darsligini (7 ta bo'lim, 17 ta dars + Maxsus mavzular) language_topics jadvaliga yuklash.
"""
import os
import sys
import glob

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

DOCKER_LANG = 'lang_1785562058041'

CHAPTERS = [
    {
        "dir": "00-bob-kirish",
        "folder": "00. Kirish",
        "lessons": [
            ("0.1-docker-nima-konteynerizatsiya.md", "0.1. Docker nima va konteynerizatsiya tushunchasi"),
            ("0.2-docker-ornatish-ubuntu.md", "0.2. Docker Engine'ni Ubuntu'ga o'rnatish"),
        ]
    },
    {
        "dir": "01-bob-asosiy-tushunchalar",
        "folder": "01. Asosiy tushunchalar",
        "lessons": [
            ("1.1-image-container-asosiy-buyruqlar.md", "1.1. Image va Container asoslari, asosiy buyruqlar"),
            ("1.2-docker-hub-image-boshqaruv.md", "1.2. Docker Hub, image qidirish va yuklab olish (pull/push)"),
            ("1.3-konteyner-loglar-exec.md", "1.3. Konteyner ichiga kirish, loglar va monitoring"),
        ]
    },
    {
        "dir": "02-bob-dockerfile",
        "folder": "02. Dockerfile",
        "lessons": [
            ("2.1-dockerfile-asoslari.md", "2.1. Dockerfile asoslari va direktivalari"),
            ("2.2-qatlamlar-build-cache.md", "2.2. Image qatlamlari (layers) va build cache"),
            ("2.3-multi-stage-build.md", "2.3. Multi-stage build"),
        ]
    },
    {
        "dir": "03-bob-malumot-tarmoq",
        "folder": "03. Ma'lumot va tarmoq",
        "lessons": [
            ("3.1-volumes-bind-mounts.md", "3.1. Volumes va bind mounts"),
            ("3.2-docker-networking.md", "3.2. Docker networking asoslari"),
        ]
    },
    {
        "dir": "04-bob-docker-compose",
        "folder": "04. Docker Compose",
        "lessons": [
            ("4.1-docker-compose-asoslari.md", "4.1. Docker Compose asoslari"),
            ("4.2-multi-service-compose-healthcheck.md", "4.2. Multi-service compose (Django + PostgreSQL + Redis, healthcheck)"),
        ]
    },
    {
        "dir": "05-bob-amaliy-loyihalar",
        "folder": "05. Amaliy loyihalar",
        "lessons": [
            ("5.1-django-konteynerlashtirish.md", "5.1. Python/Django ilovasini konteynerlashtirish"),
            ("5.2-aiogram-bot-postgresql-compose.md", "5.2. Aiogram bot + PostgreSQL Docker Compose bilan"),
            ("5.3-nginx-gunicorn-django-production.md", "5.3. Nginx + Gunicorn + Django production setup"),
        ]
    },
    {
        "dir": "06-bob-ilgor-mavzular",
        "folder": "06. Ilg'or mavzular",
        "lessons": [
            ("6.1-docker-xavfsizlik.md", "6.1. Docker xavfsizligi va eng yaxshi amaliyotlar"),
            ("6.2-tozalash-monitoring-debugging.md", "6.2. Tozalash, monitoring va debugging buyruqlari"),
            ("6.3-cicd-docker-github-actions.md", "6.3. CI/CD bilan Docker (GitHub Actions misolida)"),
        ]
    }
]

def main():
    base_dir = '/opt/yordamchi/Yordamchisayt/database/seeds/docker_darslik'
    if not os.path.exists(base_dir):
        base_dir = '/home/shamsiddin/Documents/shamsiyev/Dasturlash/Docker-Darslik'

    print(f"Baza: {DOCKER_LANG} dagi eski mavzularni tozalash...")
    db.execute("DELETE FROM language_topics WHERE lang = :l", {"l": DOCKER_LANG})

    # 1. Add "M. Maxsus mavzular"
    print("M. Maxsus mavzular qo'shilmoqda...")
    special_content = """# Maxsus mavzular

Ushbu bo'lim Docker va konteynerizatsiya bo'yicha maxsus, chuqurlashtirilgan va qo'shimcha amaliy mavzular uchun ajratilgan.

Bu yerga o'zingizning shaxsiy yoki maxsus darslaringizni qo'shishingiz mumkin."""

    db.execute(
        """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
           VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
        {
            "l": DOCKER_LANG,
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
                    "l": DOCKER_LANG,
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

    print(f"\n🎉 Yakunlandi! Jami {total_inserted} ta Docker mavzusi bazaga muvaffaqiyatli yuklandi!")

if __name__ == '__main__':
    main()
