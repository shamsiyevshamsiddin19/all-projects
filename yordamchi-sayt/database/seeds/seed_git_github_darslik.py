# -*- coding: utf-8 -*-
"""
Git & GitHub darsligini (7 ta bo'lim, 17 ta dars + Maxsus mavzular) language_topics jadvaliga yuklash.
"""
import os
import sys

sys.path.insert(0, '/opt/yordamchi/Yordamchisayt/backend_py')
from app import db

GIT_LANG = 'lang_1785565699312'

CHAPTERS = [
    {
        "dir": "00-bob-kirish",
        "folder": "00. Kirish",
        "lessons": [
            ("0.1-versiya-nazorati-git-nima.md", "0.1. Versiya nazorati va Git nima"),
            ("0.2-git-ornatish-sozlash-ubuntu.md", "0.2. Git'ni Ubuntu'ga o'rnatish va sozlash"),
        ]
    },
    {
        "dir": "01-bob-asosiy-tushunchalar",
        "folder": "01. Asosiy tushunchalar",
        "lessons": [
            ("1.1-repository-commit-asosiy-buyruqlar.md", "1.1. Repository, commit va asosiy buyruqlar"),
            ("1.2-gitignore-fayllarni-kuzatish.md", "1.2. .gitignore va fayllarni kuzatish holatlari"),
            ("1.3-commit-tarixi-diff.md", "1.3. Commit tarixini ko'rish va diff"),
        ]
    },
    {
        "dir": "02-bob-branch-merge",
        "folder": "02. Branch va Merge",
        "lessons": [
            ("2.1-branch-tushunchasi.md", "2.1. Branch tushunchasi va u bilan ishlash"),
            ("2.2-merge-va-conflict.md", "2.2. Merge va konfliktlarni hal qilish"),
            ("2.3-rebase-asoslari.md", "2.3. Rebase asoslari va merge vs rebase"),
        ]
    },
    {
        "dir": "03-bob-github",
        "folder": "03. GitHub",
        "lessons": [
            ("3.1-github-hisob-ssh-kalit.md", "3.1. GitHub hisob yaratish va SSH kalitini sozlash"),
            ("3.2-remote-push-pull-clone-fetch.md", "3.2. Remote repository: push, pull, clone va fetch"),
            ("3.3-fork-pull-request.md", "3.3. Fork va Pull Request workflow"),
        ]
    },
    {
        "dir": "04-bob-hamkorlikda-ishlash",
        "folder": "04. Hamkorlikda ishlash",
        "lessons": [
            ("4.1-git-flow-github-flow.md", "4.1. Jamoaviy ishlash workflow'lari: Git Flow va GitHub Flow"),
            ("4.2-code-review-pr-eng-yaxshi-amaliyotlar.md", "4.2. Code review va Pull Request eng yaxshi amaliyotlari"),
            ("4.3-issues-projects.md", "4.3. GitHub Issues va Projects"),
        ]
    },
    {
        "dir": "05-bob-ilgor-git",
        "folder": "05. Ilg'or Git",
        "lessons": [
            ("5.1-stash-cherry-pick-reset-revert.md", "5.1. Stash, cherry-pick va reset vs revert"),
            ("5.2-interactive-rebase-amend.md", "5.2. Interactive rebase va commit'ni tuzatish (amend)"),
            ("5.3-tags-releases.md", "5.3. Tag'lar va GitHub Releases"),
        ]
    },
    {
        "dir": "06-bob-real-loyiha",
        "folder": "06. Real loyiha",
        "lessons": [
            ("6.1-cicd-git-triggerlar.md", "6.1. CI/CD va Git trigger'lari (GitHub Actions bilan)"),
            ("6.2-django-loyihasini-git-bilan-boshqarish.md", "6.2. Django/Python loyihasini Git bilan boshqarish — amaliy misol"),
            ("6.3-troubleshooting-keng-tarqalgan-muammolar.md", "6.3. Keng tarqalgan Git muammolari va ularni hal qilish (Troubleshooting)"),
        ]
    }
]

def main():
    base_dir = '/opt/yordamchi/Yordamchisayt/database/seeds/git_github_darslik'
    if not os.path.exists(base_dir):
        base_dir = '/home/shamsiddin/Documents/shamsiyev/Dasturlash/Git-GitHub-Darslik'

    print(f"Baza: {GIT_LANG} dagi eski mavzularni tozalash...")
    db.execute("DELETE FROM language_topics WHERE lang = :l", {"l": GIT_LANG})

    # 1. Add "M. Maxsus mavzular"
    print("M. Maxsus mavzular qo'shilmoqda...")
    special_content = """# Maxsus mavzular

Ushbu bo'lim Git versiya nazorati tizimi va GitHub bo'yicha maxsus, chuqurlashtirilgan va amaliy mavzular uchun ajratilgan.

Bu yerga o'zingizning shaxsiy yoki maxsus darslaringizni qo'shishingiz mumkin."""

    db.execute(
        """INSERT INTO language_topics (lang, folder, name, content, sort_order, owner_type, owner_key, created_at, updated_at)
           VALUES (:l, :f, :n, :c, :so, :ot, :ok, NOW(), NOW())""",
        {
            "l": GIT_LANG,
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
                    "l": GIT_LANG,
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

    print(f"\n🎉 Yakunlandi! Jami {total_inserted} ta Git & GitHub mavzusi bazaga muvaffaqiyatli yuklandi!")

if __name__ == '__main__':
    main()
