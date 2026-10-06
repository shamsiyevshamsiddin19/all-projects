# Implementation Brief — Bosqich 1 (Static Hosting MVP)

> **Bu hujjat boshqa AI coding agent'ga (Claude Code, Cursor, Devin va h.k.)
> to'g'ridan-to'g'ri berish uchun yozilgan.** O'z-o'zidan yetarli — loyihani
> noldan boshlab qurish uchun kerakli hamma kontekst shu yerda. Qolgan
> `docs/01..08` fayllari — fon va kelajak bosqichlar uchun, MVP qurish
> uchun ularni o'qish shart emas (lekin link berilgan joylarda qo'shimcha
> tafsilot bor).

## 0. Nima quramiz (bir jumlada)

Foydalanuvchi GitHub/Google bilan kiradi → `git push` qiladi (yoki repo
ulaydi) → statik sayt (HTML/React/Vue/SSG build) avtomatik aniqlanadi,
build qilinadi va `https://<nom>.app.<domen>` da HTTPS bilan chiqadi.
**Hech qanday Docker konteyner yo'q.** Konteyner, backend, billing —
bu bosqichda yo'q, keyingi bosqichga qoldiriladi.

## 1. Texnologik stack (qat'iy qaror, muhokama qilinmaydi)

| Qatlam              | Texnologiya                                                                                          | Sabab                                                                                                                                            |
| ------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Backend / panel     | **Django 5 + DRF + HTMX + css+js****                                                           | `django-allauth` Google/GitHub OAuth'ni tayyor beradi                                                                                          |
| Auth                | `django-allauth`                                                                                   | Google + GitHub provider                                                                                                                         |
| DB                  | **PostgreSQL 16**                                                                              |                                                                                                                                                  |
| Navbat              | **Redis + RQ** (Celery emas)                                                                   | Oddiyroq, bizga beat/chord kerak emas                                                                                                            |
| Git qabul qilish    | Custom SSH server (Python,`paramiko` yoki `asyncssh`)                                            | Foydalanuvchiga shell berilmaydi                                                                                                                 |
| Build               | **Nixpacks** CLI chaqiriladi (`nixpacks build`)                                              | Dockerfile yozmasdan Node/Python/Go ni aniqlaydi. Lekin**toza statik HTML** uchun o'z aniqlovchimiz Nixpacks'dan oldin ishlaydi (bo'lim 4) |
| Statik serving      | **nginx** (bitta instance, regexp `server_name`)                                             | Bo'lim 6                                                                                                                                         |
| Reverse proxy / TLS | **Traefik** (yoki nginx to'g'ridan-to'g'ri — MVP'da Traefik shart emas, bo'lim 6.1 ga qarang) |                                                                                                                                                  |
| TLS                 | Let's Encrypt,**wildcard**, Cloudflare DNS-01                                                  | Bo'lim 7                                                                                                                                         |
| Frontend (panel UI) | Django templates + HTMX + Tailwind (CDN emas, build qilingan)                                        | SPA kerak emas                                                                                                                                   |
| Deploy (dev muhiti) | Docker Compose                                                                                       | Local ishlab chiqish uchun                                                                                                                       |

❌ **Ishlatilmaydi (MVP'da):** Kubernetes, Celery, Next.js/React panel UI,
Docker (foydalanuvchi ilovasi uchun), Postgres-as-a-service, billing,
Payme/Click.

## 2. Repo tuzilmasi — shuni yarating

```
hosting-platform/
├── control/                      # Django loyiha
│   ├── manage.py
│   ├── config/                   # settings, urls, wsgi/asgi
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── celery_app.py        # yo'q — RQ ishlatiladi, shu fayl kerak emas
│   ├── apps/
│   │   ├── accounts/             # allauth, SshKey model
│   │   ├── sites/                 # Site, Deployment model + build/deploy logic
│   │   └── gitreceive/            # SSH server
│   ├── static/
│   ├── templates/
│   └── requirements.txt
├── gitserver/                     # standalone SSH daemon (alohida process)
│   └── sshd.py
├── builder/                       # build worker (RQ worker sifatida ishlaydi)
│   ├── detect.py                  # statik/SPA/SSG aniqlovchi (bo'lim 4)
│   └── build.py                   # build + nginx config + symlink
├── infra/
│   ├── docker-compose.dev.yml     # dev: postgres, redis, control, builder
│   ├── nginx/
│   │   └── sites.conf.template    # bo'lim 6
│   └── README.md                  # server o'rnatish qo'llanmasi (bo'lim 9)
├── templates-starter/             # foydalanuvchiga namuna loyihalar
│   ├── plain-html/
│   ├── react-vite/
│   └── astro/
├── .env.example
├── .gitignore
└── README.md
```

⚠️ **Bu loyiha PRIVATE repo bo'lishi kerak** — `.env`, SSH host key,
OAuth client secret saqlanadi. `vibe-coding` (ochiq repo)ga qo'shilmasin.

## 3. Ma'lumotlar modeli (Django models — aynan shu maydonlar bilan boshlang)

```python
# apps/accounts/models.py
class SshKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    public_key = models.TextField(unique=True)   # "ssh-ed25519 AAAA... comment"
    fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

# apps/sites/models.py
class Site(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)          # subdomen: <slug>.app.<domen>
    repo_source = models.CharField(               # "ssh" | "github"
        max_length=16, default="ssh")
    github_repo_full_name = models.CharField(max_length=255, blank=True)
    detected_type = models.CharField(              # bo'lim 4 natijasi
        max_length=32, blank=True)                 # "plain-html" | "spa-build" | "ssr-rejected"
    build_command = models.CharField(max_length=255, blank=True)
    output_dir = models.CharField(max_length=64, default="dist")
    created_at = models.DateTimeField(auto_now_add=True)

class Deployment(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="deployments")
    commit_sha = models.CharField(max_length=40)
    status = models.CharField(max_length=16, default="queued")
        # queued | building | success | failed
    build_log = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
```

## 4. Ilova turini aniqlash — Nixpacks'dan OLDIN ishlaydigan modul

**Bu MVP'ning eng muhim qismi.** `builder/detect.py` quyidagi tartibda
tekshiradi (birinchi mos kelgani yutadi):

```python
def detect(repo_path: str) -> dict:
    """Returns {"type": str, "build_command": str|None, "output_dir": str,
    "reject_reason": str|None}"""

    # 1. package.json bor-yo'qligini tekshir
    pkg_path = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_path):
        pkg = json.load(open(pkg_path))
        scripts = pkg.get("scripts", {})
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

        # SSR red flags — build qilib bo'lmaydi, rad etiladi
        if "next" in deps and not _next_is_static_export(repo_path):
            return reject("Next.js SSR aniqlandi — bu bosqichda qo'llab-quvvatlanmaydi. "
                           "next.config.js ga output:'export' qo'shing yoki keyingi bosqichni kuting.")
        if "nuxt" in deps and "generate" not in scripts:
            return reject("Nuxt SSR aniqlandi — 'generate' script kerak (statik export).")
        if any(k in deps for k in ("express", "fastify", "@nestjs/core")):
            return reject("Backend framework aniqlandi — bu bosqichda qo'llab-quvvatlanmaydi.")

        if "build" in scripts:
            # Vite/CRA/Astro/SvelteKit-static/Angular — hammasi shu yo'ldan o'tadi
            output_dir = _guess_output_dir(repo_path, deps)  # dist/build/out/.output/public
            return {"type": "spa-build", "build_command": "npm run build",
                    "output_dir": output_dir, "reject_reason": None}

        # package.json bor, build script yo'q — static-serve qilinadigan Node loyihasi emas
        return reject("package.json topildi, lekin 'build' script yo'q.")

    # 2. requirements.txt / pyproject.toml — Python SSG (mkdocs, sphinx)
    if os.path.exists(os.path.join(repo_path, "mkdocs.yml")):
        return {"type": "spa-build", "build_command": "pip install mkdocs && mkdocs build",
                "output_dir": "site", "reject_reason": None}

    # 3. index.html root'da, package.json yo'q — toza statik
    if os.path.exists(os.path.join(repo_path, "index.html")):
        return {"type": "plain-html", "build_command": None,
                "output_dir": ".", "reject_reason": None}

    return reject("Tanish loyiha turi topilmadi. index.html yoki package.json bo'lishi kerak.")
```

**Qabul qilish mezonlari (test case'lar — shularni yozib tekshiring):**

| Repo tarkibi                                                                     | Kutilgan natija                               |
| -------------------------------------------------------------------------------- | --------------------------------------------- |
| Faqat`index.html` + `style.css`                                              | `plain-html`, build yo'q                    |
| Vite + React (`package.json` da `"build": "vite build"`, `vite.config.js`) | `spa-build`, `output_dir="dist"`          |
| CRA (`react-scripts build`)                                                    | `spa-build`, `output_dir="build"`         |
| Next.js,`next.config.js` da `output: 'export'` yo'q                          | **rad etiladi**, tushunarli xabar bilan |
| Next.js,`output: 'export'` bor                                                 | `spa-build`, `output_dir="out"`           |
| Astro standart                                                                   | `spa-build`, `output_dir="dist"`          |
| `package.json` yo'q, faqat `.py` fayllar                                     | rad etiladi                                   |

To'liq jadval va qo'shimcha frameworklar: [`docs/07-qaysi-texnologiya-qancha-ram.md`](docs/07-qaysi-texnologiya-qancha-ram.md)
bo'lim 7.4 (aniqlash qoidalari).

## 5. Deploy quvuri (end-to-end oqim)

```
1. git push <platform> main
   → gitserver/sshd.py: public key → User → Site aniqlanadi
   → git-receive-pack ishlaydi, repo /var/git/<slug>.git ga keladi
   → Deployment(status="queued") yaratiladi, RQ navbatiga tushiriladi

2. builder worker (RQ job):
   a. repo'ni /tmp/build/<deployment_id>/ ga clone qiladi (--depth=1)
   b. detect.py ishlaydi → Site.detected_type yangilanadi
      → agar reject bo'lsa: Deployment.status="failed", build_log ga sabab yoziladi, TO'XTAYDI
   c. build_command bo'lsa: sandbox'da ishga tushiriladi
      - vaqt chegarasi: 600 sekund
      - RAM chegarasi: 2 GB (cgroup yoki subprocess + resource.setrlimit)
      - tarmoq: npm registry'ga kirish kerak (to'liq izolyatsiya emas, lekin
        chiquvchi faqat 443/80 portga — MVP uchun yetarli)
   d. output_dir tekshiriladi, bo'sh bo'lsa fail
   e. /srv/sites/<slug>/releases/<sha>/ ga ko'chiriladi
   f. SPA fallback kerak-yo'qligini tekshiradi (bo'lim 6.2)
   g. symlink: /srv/sites/<slug>/current -> releases/<sha>  (atomik: ln -sfn + rename)
   h. eski release'lardan 3 tadan ortig'ini o'chiradi
   i. Deployment.status="success", finished_at=now()

3. Foydalanuvchi https://<slug>.app.<domen> ga kiradi
   → nginx Host header'dan <slug> ni oladi
   → root /srv/sites/<slug>/current/ dan faylni beradi
```

## 6. nginx konfiguratsiyasi — aynan shu fayl bilan boshlang

**Muhim: faqat BITTA nginx server bloki, hamma sayt shu orqali ishlaydi.**
Yangi sayt qo'shilganda nginx reload qilinmaydi.

```nginx
# infra/nginx/sites.conf.template
server {
    listen 443 ssl http2;
    server_name ~^(?<app>[a-z0-9][a-z0-9-]{0,61})\.app\.DOMAIN_PLACEHOLDER$;

    ssl_certificate     /etc/ssl/wildcard/fullchain.pem;
    ssl_certificate_key /etc/ssl/wildcard/privkey.pem;

    # xavfsizlik: $app faqat [a-z0-9-] bo'lishi mumkin (regexp ta'minlaydi),
    # shu sababli path traversal imkonsiz. BU REGEXP'NI KENGAYTIRMANG.
    root /srv/sites/$app/current;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;   # SPA fallback — har doim yoqilgan
    }

    location ~ /\. {
        deny all;   # .env, .git kabi fayllarni berma
    }
}

server {
    listen 80;
    server_name ~^(?<app>[a-z0-9][a-z0-9-]{0,61})\.app\.DOMAIN_PLACEHOLDER$;
    return 301 https://$host$request_uri;
}
```

### 6.1 MVP soddalashtirish: Traefik shart emas

Faqat statik serving uchun Traefik ortiqcha murakkablik. **nginx + bitta
wildcard sertifikat yetarli.** Traefik Bosqich 3'da (konteynerlar paydo
bo'lganda) kiritiladi.

### 6.2 SPA fallback avtomatik aniqlanadi

`try_files $uri $uri/ /index.html;` — bu **har doim** yoqilgan, hatto
`plain-html` turida ham (zarar qilmaydi, ko'p sahifali oddiy saytda ham
ishlaydi, chunki aniq fayl topilsa shu beriladi).

## 7. TLS — wildcard, bir marta olinadi

```bash
# certbot + Cloudflare DNS plugin
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /etc/certbot/cloudflare.ini \
  -d "*.app.DOMAIN" \
  --cert-name wildcard-app
```

⚠️ **Shart:** ilova domeni (`app.DOMAIN`) Cloudflare'da bo'lishi kerak
(DNS-01 ACME uchun API kerak). Agar asosiy domen boshqa DNS provayderda
bo'lsa — faqat `app.<domen>` subdomenini Cloudflare'ga NS orqali
delegatsiya qiling. Cron: `certbot renew` kuniga 2 marta.

## 8. SSH git receiver — asosiy xavfsizlik nuqtasi

`gitserver/sshd.py` (`asyncssh` kutubxonasi bilan):

- Har ulanish kelganda `public_key` → DB'dan `SshKey.fingerprint` orqali
  `User` topiladi
- Faqat **bitta** buyruq ruxsat etiladi: `git-receive-pack '<repo>.git'`
- ❌ PTY berilmaydi, ❌ port forwarding, ❌ agent forwarding, ❌ boshqa buyruq
- Yangi repo (`<slug>.git`) faqat shu userga tegishli papkada yaratiladi
- `post-receive` git hook → `Deployment` yozadi → RQ navbatiga tushiradi

Python namuna (asyncssh):

```python
class GitSSHServer(asyncssh.SSHServer):
    def begin_auth(self, username): return True
    def public_key_auth_supported(self): return True
    async def validate_public_key(self, username, key):
        fp = key.get_fingerprint()
        return await SshKey.objects.filter(fingerprint=fp).aexists()

async def handle_client(process):
    cmd = process.command
    if not cmd or not cmd.startswith("git-receive-pack"):
        process.exit(1); return
    repo_slug = parse_repo_name(cmd)  # faqat [a-z0-9-], boshqa belgi rad etiladi
    # git-receive-pack subprocess sifatida ishga tushiriladi, process.stdin/stdout ulanadi
```

## 9. Server o'rnatish — birinchi production node

Infratuzilma tanlovi uchun to'liq tahlil: [`docs/01-server-tanlovi.md`](docs/01-server-tanlovi.md).
MVP uchun minimal talab:

```
1 ta VPS, x86_64, Ubuntu 22.04+, 2 vCPU / 4 GB RAM yetarli
Fayl tizimi: XFS + prjquota YOQILGAN (mkfs vaqtida — keyin o'zgartirilmaydi!)
  mkfs.xfs -i size=512 /dev/xvdb   # agar alohida disk bo'lsa
  mount -o pquota /dev/xvdb /srv
Docker (faqat dev/build uchun, Nixpacks build Docker ichida ishlaydi)
nginx, certbot + python3-certbot-dns-cloudflare
PostgreSQL 16, Redis
Python 3.12, Node.js 20 (Nixpacks/npm uchun)
```

Birinchi urinish uchun: Oracle ARM free yoki Hetzner CX22 (~4€/oy)
— ikkisi ham MVP uchun yetarli. ARM'da `npm` paketlarining ba'zi
native binary'lari muammo bo'lishi mumkin — shubha bo'lsa x86 tanlang.

## 10. Qabul qilish mezonlari (Definition of Done)

- [ ] Foydalanuvchi GitHub bilan kiradi
- [ ] Panelda "SSH kalit qo'shish" — public key kiritiladi, saqlanadi
- [ ] `git remote add platform git@git.<domen>:<slug>.git && git push platform main`
  — ishlaydi, shell berilmaydi
- [ ] Toza HTML repo deploy qilinadi, 10 soniya ichida `https://<slug>.app.<domen>`
  ishlaydi, TLS to'g'ri
- [ ] Vite+React repo deploy qilinadi, build muvaffaqiyatli, SPA routing
  (`/some/deep/route`) 404 bermaydi
- [ ] Next.js (SSR, export yo'q) repo push qilinganda **tushunarli xato**
  qaytariladi ("SSR qo'llab-quvvatlanmaydi, chiqish yo'li: ...")
- [ ] Ikkinchi deploy (git push #2) — eski versiya darhol almashadi,
  downtime yo'q
- [ ] Build log panelda ko'rinadi
- [ ] Noto'g'ri SSH kalit bilan ulanish — rad etiladi
- [ ] `../../etc/passwd` kabi subdomen nomi bilan urinish — rad etiladi
  (slug validatori: `^[a-z0-9][a-z0-9-]{0,61}$`)

## 11. Bu bosqichda ATAYLAB qilinmaydigan narsalar

Boshqa AI agentga bu ro'yxatni **aniq** aytish kerak — aks holda
ko'lamdan chiqib ketadi:

- ❌ Docker konteyner ishga tushirish (foydalanuvchi ilovasi uchun)
- ❌ Backend/API/DB-per-app
- ❌ Billing, tarif, to'lov
- ❌ Telegram bot shabloni
- ❌ CLI yoki MCP server
- ❌ Mijozning o'z domeni (faqat `*.app.<domen>` subdomen)
- ❌ Jamoa/tashkilot, ko'p foydalanuvchili loyiha
- ❌ Preview deploy (PR uchun)

Bular keyingi bosqichlar — tafsilot: [`docs/06-yolmap.md`](docs/06-yolmap.md).

## 12. Qo'shimcha kontekst (kerak bo'lsa o'qing)

| Savol tug'ilsa                                                | Qarang                                                                                |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Nega bu stack tanlandi (Dokku/Coolify/k8s bilan solishtirish) | [`docs/02-ozak-tanlovi.md`](docs/02-ozak-tanlovi.md)                                 |
| To'liq arxitektura diagrammasi, kelajak komponentlar          | [`docs/03-arxitektura.md`](docs/03-arxitektura.md)                                   |
| Konteyner xavfsizligi (Bosqich 3 uchun, hozir kerak emas)     | [`docs/04-xavfsizlik.md`](docs/04-xavfsizlik.md)                                     |
| Tarif va billing rejasi (Bosqich 3)                           | [`docs/05-tariflar-va-billing.md`](docs/05-tariflar-va-billing.md)                   |
| To'liq yo'l xaritasi, keyingi bosqichlar                      | [`docs/06-yolmap.md`](docs/06-yolmap.md)                                             |
| Qaysi framework qancha RAM yeydi, to'liq jadval               | [`docs/07-qaysi-texnologiya-qancha-ram.md`](docs/07-qaysi-texnologiya-qancha-ram.md) |
| Nega statik-first, lekin statik-only emas                     | [`docs/08-zichlik-strategiyasi.md`](docs/08-zichlik-strategiyasi.md)                 |
