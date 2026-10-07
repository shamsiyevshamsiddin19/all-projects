# ⚡ MAJBURIY QOIDA (MANDATORY AI WORKSPACE DIRECTIVE)
## Avtomatik Git Commit & Push Qoidasi (GitHub Activity & Multi-Repo Sync)

Ushbu loyihalar papkasida (`/home/shamsiddin/Documents/project/loyihalar`) ishlayotgan **HAR BIR AI ASSISTANT** (Antigravity, Gemini, Cursor, Claude, Copilot, ChatGPT va boshqalar) uchun ushbu qoidalar **QAT'IY VA MAJBURIYDIR**:

---

### 1. ASOSIY TALAB (CORE REQUIREMENT)
Har qanday loyihada:
- Kod o'zgartirilganda (bug fix, refactor, yangi funksiya, dizayn yangilanishi va h.k.)
- Yangi fayl yoki yangi loyiha qo'shilganda
- Loyiha sozlamalari yangilanganda yoki xatolar tuzatilganda

**Vazifa yakunlangach DARHOL Git commit va GitHub-ga push qilinishi SHART!**  
Bu foydalanuvchining GitHub-dagi faolligini (GitHub activity / commit streak / green squares) doimiy oshirish va repozitoriyalarni to'liq sinxron saqlash uchun xizmat qiladi. Hech bir o'zgarish mahalliy kompyuterda push qilinmasdan qolib ketmasligi kerak.

---

### 2. AVTOMATIK SINXRONLASH BUYRUG'I (AUTOMATIC SYNC COMMAND)
Har qanday vazifa yoki o'zgarish kiritilgach, AI ushbu skriptni terminalda chaqirishi shart:

```bash
./sync-git.sh "feat(yoki fix/chore): o'zgarish haqida qisqa va aniq ma'lumot"
```
yoki
```bash
python3 sync-git.py "feat(yoki fix/chore): o'zgarish haqida qisqa va aniq ma'lumot"
```

Ushbu skript to'liq avtomatik tarzda:
1. `all-projects` asosiy monoreposiga o'zgarishlarni commit qilib `origin main` ga push qiladi.
2. Qaysi loyiha papkalari o'zgarganini aniqlaydi.
3. Agar o'sha loyihaning alohida mustaqil GitHub repozitoriyasi mavjud bo'lsa, o'sha repoga ham o'zgarishlarni avtomatik ravishda commit qilib push qiladi!

---

### 3. ALOHIDA REPOZITORIYALAR RO'YXATI (STANDALONE REPOS)
Agar `sync-git.sh` biror sabab bilan ishlamasa, AI qo'lda tegishli repolarga push qilishi shart:

| Papka | Alohida GitHub Repo |
| :--- | :--- |
| `15-wstore-digital-marketplace/django` | `https://github.com/shamsiyevshamsiddin19/wstore.uz.git` |
| `10-cloudnexus-hosting-platform` | `https://github.com/shamsiyevshamsiddin19/whost.uz.git` |
| `01-boostday-productivity-bot` | `https://github.com/shamsiyevshamsiddin19/boostday-bot.git` |
| `02-docforge-converter` | `https://github.com/shamsiyevshamsiddin19/docforge-converter-.git` |
| `04-cinehub-movie-bot` | `https://github.com/shamsiyevshamsiddin19/cinehub-movie-bot-.git` |
| `08-captionflow-video-bot` | `https://github.com/shamsiyevshamsiddin19/captionflow-bot-.git` |
| `11-mathcraft-web-calc` | `https://github.com/shamsiyevshamsiddin19/calculator.git` |
| `12-scarpion-music-streaming` | `https://github.com/shamsiyevshamsiddin19/SCARPION-MUSIC.git` |
| `13-shamsiyev-portfolio-hub` | `https://github.com/shamsiyevshamsiddin19/shamsiyev.uz.git` |
| `14-tictactoe-minimax-pro` | `https://github.com/shamsiyevshamsiddin19/tic-tac-toe.git` |
| `16-yordamchi-productivity-suite` | `https://github.com/shamsiyevshamsiddin19/yordamchi.git` |
| `18-paycore-gateway-sdks` | `https://github.com/shamsiyevshamsiddin19/payment-integrations.git` |
| `19-captionflow-desktop-studio` | `https://github.com/shamsiyevshamsiddin19/captionflow-desktop-.git` |

---

### 4. XAVFSIZLIK VA TOZALIK QOIDALARI (SECURITY & HYGIENE)
Commit va push qilishdan oldin QAT'IY amal qiling:
- ❌ **MAXFIY MA'LUMOTLAR:** Hech qachon `.env`, `.env.*`, kalitlar (`*.pem`, `*.key`), maxfiy API tokenlar, bot tokenlar yoki parollarni Git-ga commit qilmang!
- ❌ **ORTIQCHA FAYLLAR:** `node_modules/`, `venv/`, `.venv/`, `env/`, `__pycache__/`, `*.log`, `.DS_Store` fayllarini qo'shmang (ular `.gitignore` da belgilangan).
- ✅ **COMMIT XABARLARI:** Tushunarli va professional qilib yozing (masalan: `feat: add checkout flow`, `fix: fix hero responsiveness`).

---

### 5. YAKUNIY KO'RSATMA
Foydalanuvchiga javob qaytarishdan oldin oxirgi amalingiz o'zgarishlarni GitHub-ga push qilib (`./sync-git.sh "<xabar>"` orqali), muvaffaqiyatli yakunlanganini tekshirish bo'lsin!
