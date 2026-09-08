# Git va GitHub darsligi — Barcha mavzular (to'liq, 7 bo'lim, 17 dars)

_Ushbu darslik noldan (versiya nazorati nima ekanidan) tortib, Git'ning barcha asosiy va ilg'or vositalarini, GitHub bilan to'liq jamoaviy ishlash workflow'ini, va real Django/Python loyihasini Git orqali boshqarish, shuningdek CI/CD (GitHub Actions) bilan avtomatlashtirishgacha bo'lgan to'liq yo'lni qamrab oladi. Daraja pastdan yuqoriga: 00-bob → 06-bob. Barcha terminal buyruqlari **Ubuntu** uchun moslashtirilgan (`apt` orqali o'rnatish, SSH kalit sozlash), zamonaviy GitHub konvensiyalari (`main` standart branch, SSH/PAT autentifikatsiya, fine-grained token'lar, `gh` CLI) hisobga olingan holda, 2026-yildagi joriy holat bo'yicha tadqiqot asosida tuzilgan._

---

## 00-BOB — Kirish

| № | Mavzu | Fayl |
|---|---|---|
| 0.1 | Versiya nazorati va Git nima | 0.1-versiya-nazorati-git-nima.md |
| 0.2 | Git'ni Ubuntu'ga o'rnatish va sozlash | 0.2-git-ornatish-sozlash-ubuntu.md |

## 01-BOB — Asosiy tushunchalar

| № | Mavzu | Fayl |
|---|---|---|
| 1.1 | Repository, commit va asosiy buyruqlar | 1.1-repository-commit-asosiy-buyruqlar.md |
| 1.2 | .gitignore va fayllarni kuzatish holatlari | 1.2-gitignore-fayllarni-kuzatish.md |
| 1.3 | Commit tarixini ko'rish va diff | 1.3-commit-tarixi-diff.md |

## 02-BOB — Branch va Merge

| № | Mavzu | Fayl |
|---|---|---|
| 2.1 | Branch tushunchasi va u bilan ishlash | 2.1-branch-tushunchasi.md |
| 2.2 | Merge va konfliktlarni hal qilish | 2.2-merge-va-conflict.md |
| 2.3 | Rebase asoslari va merge vs rebase | 2.3-rebase-asoslari.md |

## 03-BOB — GitHub

| № | Mavzu | Fayl |
|---|---|---|
| 3.1 | GitHub hisob yaratish va SSH kalitini sozlash | 3.1-github-hisob-ssh-kalit.md |
| 3.2 | Remote repository: push, pull, clone va fetch | 3.2-remote-push-pull-clone-fetch.md |
| 3.3 | Fork va Pull Request workflow | 3.3-fork-pull-request.md |

## 04-BOB — Hamkorlikda ishlash

| № | Mavzu | Fayl |
|---|---|---|
| 4.1 | Jamoaviy ishlash workflow'lari: Git Flow va GitHub Flow | 4.1-git-flow-github-flow.md |
| 4.2 | Code review va Pull Request eng yaxshi amaliyotlari | 4.2-code-review-pr-eng-yaxshi-amaliyotlar.md |
| 4.3 | GitHub Issues va Projects | 4.3-issues-projects.md |

## 05-BOB — Ilg'or Git

| № | Mavzu | Fayl |
|---|---|---|
| 5.1 | Stash, cherry-pick va reset vs revert | 5.1-stash-cherry-pick-reset-revert.md |
| 5.2 | Interactive rebase va commit'ni tuzatish (amend) | 5.2-interactive-rebase-amend.md |
| 5.3 | Tag'lar va GitHub Releases | 5.3-tags-releases.md |

## 06-BOB — Real loyiha

| № | Mavzu | Fayl |
|---|---|---|
| 6.1 | CI/CD va Git trigger'lari (GitHub Actions bilan) | 6.1-cicd-git-triggerlar.md |
| 6.2 | Django/Python loyihasini Git bilan boshqarish — amaliy misol | 6.2-django-loyihasini-git-bilan-boshqarish.md |
| 6.3 | Keng tarqalgan Git muammolari va ularni hal qilish (Troubleshooting) | 6.3-troubleshooting-keng-tarqalgan-muammolar.md |

---

## Umumiy ma'lumot

- **00-bob (0.1-0.2):** Kirish — versiya nazorati muammosi, Git distributed VCS sifatida, Git va GitHub farqi, uchta asosiy soha (Working Directory/Staging Area/Repository), Ubuntu'ga `apt install git` orqali o'rnatish, `git config` orqali ism/email/editor/default branch sozlash.
- **01-bob (1.1-1.3):** Asosiy tushunchalar — `git init`/`add`/`commit`/`log`, commit hash va HEAD tushunchasi, `.gitignore` sintaksisi va Python/Django loyihalari uchun amaliy shablon, `git diff`/`git show` orqali o'zgarishlarni tahlil qilish.
- **02-bob (2.1-2.3):** Branch va Merge — `git switch`/`git branch` orqali mustaqil ish yo'nalishlari yaratish, fast-forward va 3-way merge, konflikt yuzaga kelishi va uni qo'lda hal qilish, rebase orqali tekis tarix hosil qilish va uning xavfsizlik qoidalari.
- **03-bob (3.1-3.3):** GitHub — SSH kalit (`ed25519`) va Personal Access Token orqali xavfsiz autentifikatsiya, `git remote`/`push`/`pull`/`clone`/`fetch` orqali masofadagi repository bilan ishlash, fork va Pull Request orqali ochiq-manba loyihalarga hissa qo'shish jarayoni.
- **04-bob (4.1-4.3):** Hamkorlikda ishlash — GitHub Flow (sodda, tez-tez deploy) va Git Flow (rasmiy versiyalangan release'lar) workflow'larini taqqoslash, sifatli code review va Pull Request yozish amaliyotlari, branch protection qoidalari, Issues va Projects orqali vazifalarni boshqarish.
- **05-bob (5.1-5.3):** Ilg'or Git — `stash` orqali ishni vaqtincha to'xtatish, `cherry-pick` orqali muayyan commit'ni ko'chirish, `reset` (soft/mixed/hard) va `revert` orasidagi muhim farq, interactive rebase orqali commit tarixini tozalash, tag'lar va Semantik Versiyalash orqali GitHub Release'lar yaratish.
- **06-bob (6.1-6.3):** Real loyiha — GitHub Actions'ning Git voqealariga (push/PR/tag) qanday bog'lanishini, to'liq Django loyihasini Git bilan (`.env`, migratsiyalar, branch strategiyasi) boshqarishning amaliy misolini, va eng ko'p uchraydigan Git xatolarining tekshirilgan yechimlarini o'z ichiga oladi.
- **Jami: 17 dars** (0.1 dan 6.3 gacha), noldan to'liq jamoaviy Git/GitHub workflow bilimigacha to'liq qamrab olingan.
- Har bir dars bir xil tuzilmaga ega: **Bu darsda nimalarni o'rganasiz** → **Nazariy qism** → **Amaliy misol** → **Keng tarqalgan xatolar** (har biri ❌/✅ va SABAB bilan) → **Mashq/topshiriq** (Oson/O'rtacha/Qiyin, javoblari bilan) → **Qisqacha xulosa**.
- Barcha terminal buyruqlari Ubuntu uchun moslashtirilgan (`apt`, `ssh-keygen`, `gh` CLI'ning rasmiy apt repozitoriyasi orqali o'rnatilishi); darslik siz avval yaratgan **Python darsligi** (virtual muhitlar, `pytest`), **Django darsligi** va **Docker darsligi** (GitHub Actions, konteynerizatsiya) bilimlariga tayangan holda, ularni to'liq Git versiya nazorati va GitHub jamoaviy workflow muhitida qanday boshqarish va avtomatlashtirishni o'rgatadi.
