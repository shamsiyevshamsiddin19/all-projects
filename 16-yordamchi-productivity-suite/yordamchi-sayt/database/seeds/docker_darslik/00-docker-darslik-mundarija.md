# Docker darsligi — Barcha mavzular (to'liq, 7 bo'lim, 17 dars)

_Ushbu darslik noldan (Docker nima ekanidan) tortib, production darajadagi Django+Aiogram+PostgreSQL+Nginx tizimini Docker Compose orqali qurish va GitHub Actions bilan CI/CD avtomatlashtirishgacha bo'lgan to'liq yo'lni qamrab oladi. Daraja pastdan yuqoriga: 00-bob → 06-bob. Barcha terminal buyruqlari **Ubuntu** (Debian-asosidagi distributivlar) uchun moslashtirilgan, zamonaviy `docker compose` (plagin, bo'sh joy bilan — eski `docker-compose` emas) sintaksisi ishlatilgan. Mavzular tarkibi 2026-yildagi joriy Docker holati (rasmiy `apt` repozitoriyasi orqali o'rnatish, `compose.yaml`da `version:` kaliti endi shart emasligi) bo'yicha tadqiqot asosida tuzilgan._

---

## 00-BOB — Kirish

| № | Mavzu | Fayl |
|---|---|---|
| 0.1 | Docker nima va konteynerizatsiya tushunchasi | 0.1-docker-nima-konteynerizatsiya.md |
| 0.2 | Docker Engine'ni Ubuntu'ga o'rnatish | 0.2-docker-ornatish-ubuntu.md |

## 01-BOB — Asosiy tushunchalar

| № | Mavzu | Fayl |
|---|---|---|
| 1.1 | Image va Container asoslari, asosiy buyruqlar | 1.1-image-container-asosiy-buyruqlar.md |
| 1.2 | Docker Hub, image qidirish va yuklab olish (pull/push) | 1.2-docker-hub-image-boshqaruv.md |
| 1.3 | Konteyner ichiga kirish, loglar va monitoring | 1.3-konteyner-loglar-exec.md |

## 02-BOB — Dockerfile

| № | Mavzu | Fayl |
|---|---|---|
| 2.1 | Dockerfile asoslari va direktivalari | 2.1-dockerfile-asoslari.md |
| 2.2 | Image qatlamlari (layers) va build cache | 2.2-qatlamlar-build-cache.md |
| 2.3 | Multi-stage build | 2.3-multi-stage-build.md |

## 03-BOB — Ma'lumot va tarmoq

| № | Mavzu | Fayl |
|---|---|---|
| 3.1 | Volumes va bind mounts | 3.1-volumes-bind-mounts.md |
| 3.2 | Docker networking asoslari | 3.2-docker-networking.md |

## 04-BOB — Docker Compose

| № | Mavzu | Fayl |
|---|---|---|
| 4.1 | Docker Compose asoslari | 4.1-docker-compose-asoslari.md |
| 4.2 | Multi-service compose (Django + PostgreSQL + Redis, healthcheck) | 4.2-multi-service-compose-healthcheck.md |

## 05-BOB — Amaliy loyihalar

| № | Mavzu | Fayl |
|---|---|---|
| 5.1 | Python/Django ilovasini konteynerlashtirish | 5.1-django-konteynerlashtirish.md |
| 5.2 | Aiogram bot + PostgreSQL Docker Compose bilan | 5.2-aiogram-bot-postgresql-compose.md |
| 5.3 | Nginx + Gunicorn + Django production setup | 5.3-nginx-gunicorn-django-production.md |

## 06-BOB — Ilg'or mavzular

| № | Mavzu | Fayl |
|---|---|---|
| 6.1 | Docker xavfsizligi va eng yaxshi amaliyotlar | 6.1-docker-xavfsizlik.md |
| 6.2 | Tozalash, monitoring va debugging buyruqlari | 6.2-tozalash-monitoring-debugging.md |
| 6.3 | CI/CD bilan Docker (GitHub Actions misolida) | 6.3-cicd-docker-github-actions.md |

---

## Umumiy ma'lumot

- **00-bob (0.1-0.2):** Kirish — konteynerizatsiya tushunchasi, Docker va virtual mashina farqi, Image/Container/Registry asosiy tushunchalari, Ubuntu'ga rasmiy `apt` repozitoriyasi orqali o'rnatish, `sudo`siz ishlatish uchun `docker` guruhi.
- **01-bob (1.1-1.3):** Asosiy tushunchalar — `docker run`/`ps`/`stop`/`rm`, port mapping, Docker Hub va tag (`latest`dan saqlanish), `docker logs`/`exec`/`inspect`/`stats` orqali diagnostika.
- **02-bob (2.1-2.3):** Dockerfile — `FROM`/`WORKDIR`/`COPY`/`RUN`/`CMD`/`ENTRYPOINT`, image qatlamlari va build cache optimallashtirish, multi-stage build orqali image hajmini kamaytirish.
- **03-bob (3.1-3.2):** Ma'lumot va tarmoq — volume (Docker boshqaradi) va bind mount (development uchun) farqi, maxsus Docker tarmoqlari va konteynerlar orasidagi DNS orqali nom bilan bog'lanish.
- **04-bob (4.1-4.2):** Docker Compose — `compose.yaml` (zamonaviy format, `version:` kaliti shart emas), `depends_on`, `healthcheck` bilan xizmatning haqiqiy tayyorligini kutish, `.env` orqali maxfiy ma'lumotlarni boshqarish.
- **05-bob (5.1-5.3):** Amaliy loyihalar — Django'ni to'liq konteynerlashtirish (`entrypoint.sh`, dev/prod compose fayllari), Aiogram bot + Django + umumiy PostgreSQL (migratsiya alohida xizmat sifatida, `restart` siyosati), Nginx+Gunicorn production arxitekturasi (statik fayllar uchun umumiy volume, `expose` vs `ports`).
- **06-bob (6.1-6.3):** Ilg'or mavzular — xavfsizlik (`USER`, `secrets`, `docker scout`), resurslarni tozalash va production diagnostikasi (`prune`, OOM tekshiruvi), GitHub Actions orqali to'liq CI/CD (avtomatik test + Docker Hub'ga yuklash).
- **Jami: 17 dars** (0.1 dan 6.3 gacha), noldan production darajadagi Docker/Docker Compose bilimigacha to'liq qamrab olingan.
- Har bir dars bir xil tuzilmaga ega: **Bu darsda nimalarni o'rganasiz** → **Nazariy qism** → **Amaliy misol** → **Keng tarqalgan xatolar** (har biri ❌/✅ va SABAB bilan) → **Mashq/topshiriq** (Oson/O'rtacha/Qiyin, javoblari bilan) → **Qisqacha xulosa**.
- Barcha terminal buyruqlari Ubuntu (apt, `docker compose` — bo'sh joy bilan) uchun moslashtirilgan; darslik siz avval yaratgan **Python darsligi** (o'zgaruvchilar, funksiyalar, OOP, istisnolar, `pytest`) va **Django darsligi** (Django asoslari, Django+Aiogram+PostgreSQL integratsiyasi) bilimlariga tayangan holda, ularni to'liq Docker/Docker Compose muhitida konteynerlashtirish va production'ga chiqarishni o'rgatadi.
