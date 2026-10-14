# Instagram aqlli bot 🤖

Instagram akkauntingizga kelgan **DM**, **story mention** va **post izohlariga**
Google Gemini yordamida avtomatik, aqlli javob beradigan bot.

Bu bot **rasmiy Instagram Graph API** orqali ishlaydi — ya'ni akkauntingiz
bloklanmaydi (login/parol talab qilmaydi).

---

## ⚠️ Muhim shart

Rasmiy API DM javob berish uchun quyidagilar **kerak**:

1. **Instagram Professional (Business yoki Creator) akkaunt** ✅ (sizda bor)
2. Akkaunt bir **Facebook sahifasiga** ulangan bo'lishi kerak
3. **Meta Developer** ilovasi (bepul)

Facebook sahifasi bo'lmasa — Instagram sozlamalaridan bepul yaratsangiz bo'ladi.

---

## 1-qadam: Kerakli dasturlar

- [Python 3.10+](https://www.python.org/downloads/) o'rnating
- Terminalda loyiha papkasiga kiring:

```bash
cd E:\instagram-bot
pip install -r requirements.txt
```

---

## 2-qadam: Gemini tokenini oling (bepul)

1. https://aistudio.google.com/apikey saytiga kiring
2. **"Create API key"** tugmasini bosing
3. Chiqqan kalitni nusxalang

---

## 3-qadam: Meta Developer sozlash

1. https://developers.facebook.com → **My Apps** → **Create App**
2. App turini **"Business"** deb tanlang
3. Ilovaga **Instagram** mahsulotini qo'shing
4. Instagram akkauntingizni Facebook sahifasiga ulang
5. Quyidagilarni oling:
   - **Instagram Access Token** (uzoq muddatli token oling)
   - **Instagram Account ID** (Business account ID)
6. Webhook obunasida quyidagilarni yoqing:
   - `messages` (DM uchun)
   - `comments` (izohlar uchun)
   - `message_reactions`, `messaging_postbacks` (ixtiyoriy)

> Batafsil: https://developers.facebook.com/docs/instagram-platform

---

## 4-qadam: Sozlamalarni to'ldiring

`.env.example` faylini nusxalab `.env` deb nomlang va ichini to'ldiring:

```bash
copy .env.example .env      # Windows
```

`.env` ichida:
- `IG_ACCESS_TOKEN` — Meta'dan olingan token
- `IG_ACCOUNT_ID` — Instagram Business account ID
- `GEMINI_API_KEY` — Gemini tokeni
- `VERIFY_TOKEN` — o'zingiz o'ylab topgan maxfiy so'z
- `BOT_PERSONA` — bot qanday gapirsin (o'zingizga moslang)

---

## 5-qadam: Botni ishga tushiring

```bash
python app.py
```

Bot `http://localhost:5000` da ishlaydi.

### Webhook'ni internetga chiqarish

Meta webhook'ni ko'rishi uchun kompyuteringiz internetdan ko'rinishi kerak.
Eng osoni — **ngrok**:

1. https://ngrok.com dan yuklab oling
2. Ishga tushiring:
   ```bash
   ngrok http 5000
   ```
3. Chiqqan `https://....ngrok-free.app` manzilini oling
4. Meta Developer → Webhooks → **Callback URL**:
   `https://....ngrok-free.app/webhook`
   **Verify Token**: `.env` dagi `VERIFY_TOKEN` bilan bir xil

---

## Bot nima qiladi?

| Hodisa | Bot javobi |
|--------|-----------|
| Kimdir DM yozdi | Gemini aqlli javob yozadi |
| Sizni story'da belgiladi | Avtomatik rahmat xabari |
| Postingizga izoh yozdi | Izohga aqlli javob |

Botning "shaxsini" o'zgartirish uchun `.env` dagi `BOT_PERSONA` ni tahrirlang.

---

## Tez-tez uchraydigan savollar

**Bot javob bermayapti?**
- `.env` to'g'ri to'ldirilganini tekshiring
- Terminaldagi xato xabarlarini o'qing
- Meta'da webhook `messages`/`comments` ga obuna bo'lganini tekshiring

**Xavfsizmi?**
- Ha. Bu rasmiy Meta API. Login/parol ishlatilmaydi, shuning uchun
  akkaunt bloklanmaydi.

**Token muddati tugadimi?**
- Instagram access token muddatini uzun qilib (long-lived) oling.
```
