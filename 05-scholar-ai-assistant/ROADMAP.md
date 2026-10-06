# MUSTAQILBOT — Kuchaytirish rejasi va ish prompti

> Bu fayl Claude (yoki boshqa AI-agent) uchun yozilgan **o'z-o'ziga ish prompti**.
> Har sessiyada shu fayldan boshlab ishlanadi: navbatdagi `[ ]` bosqich olinadi,
> bajariladi, sinaladi, deploy qilinadi, `[x]` belgilanadi.

---

## 0. MISSIYA VA ISH USLUBI (kuchli prompt)

Sen O'zbekiston talabalari uchun akademik hujjatlar yozib beruvchi Telegram-bot
(@talabaxizmatlaribot) ustida ishlaydigan katta dasturchi-muhandissan. Maqsad —
**bozordagi eng kuchli bot**: o'qituvchi hujjatni ko'rganda "zo'r" deydigan sifat.

Ish qoidalari:
1. **Har bosqich to'liq sikl**: kod → lokal test → deploy → serverda jonli sinov →
   natijani o'lchash → ROADMAP'da belgilash. Yarim bajarilgan bosqich qoldirma.
2. **Sifatni taxmin qilma — o'lcha.** Hujjat sinovi = so'z soni + jadval/grafik/formula
   soni + faylni lokalga ko'chirib foydalanuvchiga ko'rsatish.
3. **Promptlar va kod birga kuchayadi**: AI'dan yangi element so'rasang, avval
   builder o'sha elementni chiroyli chiqarishiga ishonch hosil qil.
4. **AI'ga ishonma, kodga ishon**: format qat'iy bo'lishi kerak joyda (titul, mundarija
   raqamlari, sana) — kod yozsin, AI emas.
5. Har muvaffaqiyatsizlikda log o'qi (`journalctl -u mustaqilbot`), taxmin qilma.
6. Ishning oxirida xotira faylini (`mustaqilbot-deploy.md`) yangila.

---

## 1. ARXITEKTURA XARITASI

| Fayl | Vazifa |
|---|---|
| `ai/prompts.py` | Barcha AI promptlari; `_subject_hint()` fanga xos, `_visuals()` kvotalar, chunk_* bo'laklab yozish, `_OVERSHOOT=1.15` kalibrlash, 1 bet = 300 so'z |
| `ai/provider.py` | Claude (streaming) + OpenAI zaxira; typed xatolar |
| `services/generator.py` | Buyurtma → AI → fayl. 10+ bet = bo'laklab (intro/boblar/final), o'lchab-to'ldirish (90% dan kam bob → `chunk_extend`) |
| `docs/md_blocks.py` | Markdown parser: jadval, `$$formula$$`, ```` ```chart ````, sarlavha, ro'yxat |
| `docs/charts.py` | Pillow grafiklar (bar/line/pie) — matplotlib YO'Q (ataylab!) |
| `docs/docx_builder.py` | DOCX: Word jadvallar, formulalar, grafik PNG, ichki qalin |
| `docs/pdf_builder.py` | PDF (reportlab): shu elementlar |
| `docs/pptx_builder.py` | Slaydlar (hali oddiy) |
| `bot/handlers/order.py` | Buyurtma FSM oqimi, `_generate_and_send()` |
| `bot/states/order.py`, `bot/keyboards/inline.py` | FSM holatlar, tugmalar |
| `db/models.py`, `db/crud.py` | SQLAlchemy (PostgreSQL), orders/users/payments |
| `config.py` | Sozlamalar, `DOC_TYPES` (narx, bet oralig'i), admin override'lar |
| `web/admin.py` | aiohttp admin panel (port 8092) |

## 2. QAT'IY CHEKLOVLAR

- **Server**: shamsiyev (141.147.156.65), Oracle Micro, **498MB RAM**, systemd
  `MemoryHigh=140M` bot uchun. OG'IR KUTUBXONALAR TAQIQLANADI (matplotlib, numpy,
  pandas...). Faqat yengil sof-Python paketlar.
- **Deploy**: o'zgargan fayllardan tar → scp `/tmp` → serverda ochish → `_backups/` ga
  zaxira → `.venv/bin/python -m py_compile` + import test → `sudo systemctl restart
  mustaqilbot` → `journalctl` tekshirish. Serverdagi `.env` va bazani HECH QACHON almashtirma.
- **SSH**: `ssh -i ~/.ssh/oracle_ssh opc@141.147.156.65`, operatsiyalar bittalab.
- **Xarajat**: har to'liq sinov generatsiyasi ~$0.2-0.5. Sinovni 10 bet bilan qil,
  natijani lokalga ko'chirib foydalanuvchiga ber.
- **Zaxira provayder**: OpenAI (gpt-4o-mini, 16K chiqish chegarasi) — yangi imkoniyat
  qo'shganda fallback yo'li buzilmasin (web search OpenAI'da yo'q — guard qo'y).

---

## 3. BOSQICHLAR

Tavsiya etilgan tartib: **A → J → B → C → K → D → E → F → G → L → H**
(A+J birga xabarlarga tegadi; B/C sifat yadrosi; K uchun J dagi baho/share tayyor
bo'lishi kerak; L broadcast K dagi segment ustunlariga tayanadi).

### [x] A. Titul varag'i + jonli progress (1 kunlik, darrov seziladi)

**A1. Titul varag'i (kod bilan, AI'siz):**
- `bot/handlers/order.py` + `bot/states/order.py`: buyurtmada yangi savol — «OTM nomi»
  (masalan: Toshkent davlat iqtisodiyot universiteti). Ixtiyoriy, «O'tkazib yuborish»
  tugmasi bilan. `details['otm']` ga saqlanadi. Kafedra ham ixtiyoriy so'ralsin.
- `docs/docx_builder.py`: `add_title_page(doc, meta)` — standart joylashuv:
  - Tepada markazda: O'ZBEKISTON RESPUBLIKASI OLIY TA'LIM, FAN VA INNOVATSIYALAR VAZIRLIGI
  - OTM nomi (katta harf), kafedra
  - O'rtada: hujjat turi (MUSTAQIL ISH / KURS ISHI / ...), «Mavzu: ...» (qalin, 16pt)
  - Pastroq o'ngda: Bajardi: F.I.O (guruh), Ilmiy rahbar (bo'lsa), Fan
  - Eng pastda markazda: Toshkent — 2026 (yil dinamik: `datetime.now().year`)
  - Sahifa raqami titulda ko'rinmasin (birinchi sectionda different first page yoki
    footer'ni bo'sh qoldirish), keyin `add_page_break`.
- `docs/pdf_builder.py`: xuddi shu titul (Spacer + markazlangan paragraflar + PageBreak).
- `services/generator.py`: `build_docx(text, path, topic, meta=...)` ga meta uzatish.
- `ai/prompts.py`: chunk_intro va bir martalik promptlardan titul qismini OLIB TASHLASH
  (endi kod yasaydi) — AI faqat mundarija+kirishdan boshlasin. Eski `# SARLAVHA` va
  «**Mavzu:**» qatorlari so'ralmasin.
- **Qabul testi**: 10 betlik sinov hujjatida to'liq titul varag'i, undan keyin yangi
  betdan mundarija; titul ma'lumotlari buyurtmadagiga aynan mos.

**A2. Jonli progress:**
- `services/generator.py`: `generate_document(..., progress=None)` — `async def
  progress(text)` callback; bo'laklab rejimda har bosqichda chaqirilsin
  («📑 Reja va kirish...», «📝 II bob yozilmoqda (3/5)...», «📊 Fayl yasalmoqda...»).
- `bot/handlers/order.py` `_generate_and_send`: status xabarini yaratib, callbackda
  `edit_text` qilish. Muhim: editlar orasida ≥3s (Telegram limit), `try/except
  TelegramBadRequest` (bir xil matn xatosi), xabar oxirida o'chirilsin yoki
  «✅ Tayyor!» ga aylansin.
- **Qabul testi**: botdan real buyurtma — xabar bosqichma-bosqich yangilanadi.

### [x] B. LaTeX formulalar — haqiqiy Word tenglamalari

Hozir formulalar Unicode matn ($$ x² $$ → kursiv matn). Maqsad: AI LaTeX yozadi,
DOCX'da **Word'ning haqiqiy (native, tahrirlash mumkin) tenglamasi** chiqadi —
kasrlar, ildizlar, integrallar, matritsalar professional ko'rinishda.

- **Texnologiya (yengil, sof Python — serverga mos):**
  `latex2mathml` (LaTeX → MathML) + `mathml2omml` (MathML → Word OMML XML) →
  OMML elementini python-docx paragraf XML'iga joylash. Ikkalasi kichik sof-Python
  paket. AVVAL tekshir: `pip index`/`pip install` bilan mavjudligini va litsenziyasini;
  agar `mathml2omml` yaroqsiz bo'lsa — zaxira yo'l: `lxml` (python-docx bilan birga
  keladi) + MML2OMML.XSL uslubnoma orqali XSLT.
- `docs/docx_builder.py` `_add_formula()`:
  1. LaTeX → OMML muvaffaqiyatli → markazda native tenglama;
  2. konvertatsiya xatosi → hozirgi Unicode-kursiv fallback (hech qachon yiqilmasin).
- `docs/pdf_builder.py`: PDF uchun `pylatexenc.latex2text` bilan LaTeX → chiroyli
  Unicode matn (PDF ikkilamchi format, DOCX'ga fallback bor).
- `docs/md_blocks.py`: `$$...$$` parseri qoladi; QO'SHIMCHA: ichki (inline) formula
  `\( ... \)` ko'rinishida — para ichida aniqlansa, docx'da run-darajali OMML
  (v1da shart emas, blok formulalar yetarli — inline'ni oxirida qil).
- `ai/prompts.py` 7-qoida YANGILANADI: endi $$...$$ ichida TO'LIQ LaTeX ruxsat va
  tavsiya etiladi: `\frac{a}{b}`, `\sqrt{x}`, `\sum_{i=1}^{n}`, `\int_a^b`, `x_1`,
  `\alpha`, matritsalar. Misollar bilan. Unicode ham qabul qilinadi (fallback).
  `_subject_hint`: matematika/fizika/kimyo uchun formulalar soni talabi oshirilsin.
- `requirements.txt`: `latex2mathml`, `mathml2omml`, `pylatexenc` qo'shish; serverda
  `.venv/bin/pip install` (RAM yengil — sof Python).
- **Qabul testi**: lokalda sinov markdown: `$$ \frac{-b \pm \sqrt{b^2-4ac}}{2a} $$`,
  `$$ \int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2} $$`, `$$ \sum_{i=1}^{n} x_i $$`
  → DOCX'ni Word'da ochganda haqiqiy tenglama ko'rinadi (lokalga ko'chirib foydalanuvchiga
  ber). Serverda «Oliy matematika» fanidan 10 betlik jonli sinov — kamida 4 native formula.

### [x] C. Web search — haqiqiy manbalar va statistika

- `ai/provider.py`: yangi `generate_with_search(system, user, max_tokens, max_searches=4)` —
  Claude server-side web search: `tools=[{"type": "web_search_20260209", "name": "web_search",
  "max_uses": 4}]`. MUHIM: `stop_reason == "pause_turn"` bo'lsa assistant javobini
  history'ga qo'shib qayta yuborish (maks 5 marta). Streaming bilan sinab ko'r; muammo
  bo'lsa non-streaming (chunk chiqishi ≤8K token — timeout xavfi past).
  OpenAI fallback'da search YO'Q — oddiy `generate()` ga tushsin.
- Qayerda ishlatiladi (xarajat nazorati):
  - `chunk_final` (adabiyotlar) — HAR DOIM: real manbalar, real URL/DOI, lex.uz qonunlari;
  - tahliliy boblar (`done_labels` bo'lgan chunk_body) — kurs/diplom/maqolada: real
    statistika (stat.uz va h.k.);
  - kichik ishlar (referat/mustaqil <10 bet) — faqat adabiyotlar uchun 1-2 qidiruv.
- `config.py`: `WEB_SEARCH=1` env flag (o'chirish imkoni).
- `ai/prompts.py`: search ishlatiladigan promptlarga: «Internetdan REAL manbalarni toping
  va aynan topilganlarni keltiring; topilmasa taxminiy manba TO'QIMANG, klassik darsliklarni
  yozing. Statistikani manba nomi va yili bilan keltiring.»
- **Qabul testi**: iqtisod fanidan jonli sinov — adabiyotlarda real nashrlar/URLlar;
  logda web_search ishlatilgani ko'rinadi; xarajat oshgani hisoblab foydalanuvchiga aytilsin.

### [x] D. Premium tarif (kuchli model)

- `config.py`: `CLAUDE_MODEL_PREMIUM` env (default `claude-opus-4-6`), `DOC_TYPES` ga
  premium narx koeffitsienti (2.0x, admin override qilinadigan `premium_mult` kaliti).
- `bot/handlers/order.py`: bet sonidan keyin «Sifat darajasi: ⚡ Standart / 👑 Premium
  (+100%, kuchliroq AI)» tugmalari; `details['tier']`.
- `ai/provider.py`: `generate(..., model=None)` — override; `services/generator.py`
  tier'ga qarab modelni uzatadi (BARCHA chunk chaqiruvlariga).
- Premium'da `_OVERSHOOT` ni alohida kalibrlash (opus boshqacha yozishi mumkin — sinab o'lcha).
- **Qabul testi**: premium buyurtma logda opus modeli bilan ketadi, narx 2x hisoblanadi.

### [ ] E. Reja tasdiqlash (kurs/diplom uchun)

- Oqim: to'lovdan keyin avval FAQAT intro (mundarija+kirish) generatsiya qilinadi →
  mundarija foydalanuvchiga xabar qilib yuboriladi → tugmalar: «✅ Shu reja bilan yoz» /
  «✏️ O'zgartirish kiritish» (foydalanuvchi matnda izoh yozadi → intro qayta
  generatsiya, 1 marta bepul).
- Texnika: `orders` jadvaliga `intro_text TEXT` ustuni (ALTER TABLE try/except
  migratsiya, tatu-bots uslubida `db/crud.py` da). FSM yangi holat
  `OrderState.plan_review`. Tasdiqdan keyin qolgan bo'laklar yoziladi.
- Faqat `kurs`, `diplom` (qimmat buyurtmalar); boshqalarga to'g'ridan-to'g'ri.
- Foydalanuvchi 30 daqiqada javob bermasa — avtomatik davom ettirish (asyncio timer
  yoki keyingi /start da tekshirish).
- **Qabul testi**: kurs ishi buyurtmasida mundarija keladi, o'zgartirish so'ralsa
  yangi reja, tasdiqdan keyin to'liq hujjat.

### [x] F. Qayta ishlash (revizyon)

- `orders` jadvaliga `source_text TEXT` (yakuniy markdown) — generatsiyadan keyin saqlash.
- `order_done_kb` ga «✏️ Qayta ishlash» tugmasi → foydalanuvchi o'qituvchi izohini
  yozadi → AI'ga: to'liq matn + izoh → «faqat tegishli qismlarni qayta yoz, qolganini
  AYNAN saqla» prompti (yangi `prompts.revise()`) → fayl qayta yasab yuboriladi.
- Limit: har buyurtmaga 2 ta bepul revizyon (`orders.revisions INT DEFAULT 0`).
- Diqqat: source_text katta (50-100KB) — TEXT ustun PostgreSQL'da muammosiz.
- **Qabul testi**: tayyor buyurtmada izoh yuborilsa yangilangan fayl keladi, 3-chi
  urinishda «limit tugadi» xabari.

### [x] G. Navbat + admin ogohlantirishlari

- `services/generator.py` (yoki yangi `services/queue.py`): global
  `asyncio.Semaphore(1)` + kutayotganlar hisobchisi. Band bo'lsa foydalanuvchiga
  «⏳ Navbatdasiz: N-o'rin» (progress xabari orqali).
- `bot/handlers/order.py` except blokida: `settings.admin_ids` ga xato tafsiloti
  (buyurtma ID, foydalanuvchi, hujjat turi, xatoning 1-qatori) DM yuborish.
  Claude→OpenAI fallback ishga tushganda ham adminга bildirish (kunига 1 marta, spam emas).
- **Qabul testi**: 2 parallel buyurtma ketma-ket bajariladi; sun'iy xato adminга DM keladi.

### [ ] H. Slaydlarni kuchaytirish

- `ai/prompts.py` slayd prompti: har slaydga ixtiyoriy `"chart": {...}` (charts.py
  formati) va `"layout": "title|content|two_col|chart|quote|end"`.
- `docs/pptx_builder.py`: chart bo'lsa `docs/charts.py` bilan PNG chizib slaydga
  joylash; 3 ta rang-mavzu (ko'k-professional / yashil-tabiiy / to'q-minimal) —
  fanга qarab tanlash; two_col layout; oxirgi slayd dizayni.
- **Qabul testi**: 12 slaydlik sinov PPTX — kamida 2 slaydda diagramma, mavzuga mos ranglar.

### [x] J. Bot xabarlari va UX (copywriting + psixologiya)

Barcha foydalanuvchi ko'radigan matnlar (`bot/handlers/*.py`, `bot/keyboards/inline.py`)
bir ovozda qayta yoziladi: samimiy, ishonchli, har xabarda BITTA aniq keyingi qadam (CTA).

- **YOLG'ON VA'DANI TUZATISH (birinchi navbatda!)**: «Tayyor bo'lishi: 30-90 soniya»
  endi noto'g'ri — bo'laklab generatsiya daqiqalar oladi. Yangi ramka: «⏱ 5-10 daqiqa —
  chunki har bob alohida, jadval-grafiklari bilan sifatli yoziladi» + jonli progress (A2).
  Sekinlik kamchilik emas, SIFAT DALILI sifatida sotilsin.
- **/start ijtimoiy isbot**: DB'dan JONLI raqamlar («📊 Shu paytgacha N ta hujjat,
  M talabaga») — soxta hisoblagich EMAS, `orders_count` so'rovi.
- **Xato xabarlari ushlab qolsin**: «Xato yuz berdi» + darrov «🔄 Qayta urinish»
  tugmasi (bir bosishda o'sha buyurtma qayta), «pul qaytdi» ta'kidlansin (ishonch).
- **Yetkazilgandan keyin baho**: ⭐1-5 inline tugmalar (`ratings` jadvali — ALTER
  migratsiya). 4-5 yulduz bosganda → «Do'stlaringga ulash» (tayyor share-matn +
  referal havola — Telegram share url). 1-3 yulduz → «Nima yoqmadi?» + adminга DM.
- **Narx psixologiyasi**: narx yonida qiymat («📄 12 bet + 2 jadval + grafik = 20 000
  so'm»); katta ishlar oldida «bo'lib to'lash» sifatida balans to'ldirish taklifi.
- **Buyurtma oqimida ishonch**: mavzu kiritilganda «Zo'r mavzu tanladingiz 👍» kabi
  mikro-tasdiqlar; to'lovdan oldin xulosa-karta (hamma detal bir xabarda).
- Qoida: barcha raqam va muddatlar HAQIQIY bo'lsin — soxta chegirma/hisoblagich
  taqiqlanadi (aniqlansa ishonch qaytmaydi).

### [ ] K. O'sish mexanikalari (marketing dvigateli)

- **Welcome-bonus**: yangi foydalanuvchiga 5 000 so'm balans (settings orqali
  sozlanadigan) — eng arzon ishdan biroz kam: «to'ldirsang yetadi» effekti
  (reciprocity + aktivatsiya). `_WELCOME` da ko'rsatilsin.
- **Cashback**: har buyurtmadan 3-5% balansга qaytsin («keyingi ishingga chegirma
  yig'ilyapti») — qayta buyurtma sababi. config + payment oqimiga kiritish.
- **Promo-kodlar**: `promo_codes` jadvali (kod, turi: % yoki so'm, muddat, limit,
  ishlatilgan soni); buyurtma to'lovida «🎟 Promo-kod» tugmasi; admin panelda yaratish.
- **Eslatmalar (re-engagement)** — `main.py` da soatlik asyncio fon jobi:
  - buyurtma boshlangan, to'lanmagan (2 soat) → «Hujjating kutib turibdi» + kichik promo;
  - 7-14 kun faolsiz (`users.last_active`) → foydali xabar + taklif;
  - mavsumiy kampaniya (sessiya: dek-yan, may-iyun) — kuchli davr;
  - QOIDA: har foydalanuvchiga haftasiga MAKS 1 marketing xabar; /stop bilan
    o'chirish imkoni (`users.marketing_ok BOOLEAN` migratsiya). Spam = ban = o'lim.
- **Referal gamifikatsiya**: haftalik TOP-5 taklifchilar reytingi + g'olibga bonus;
  referal sahifasida jonli statistika («Siz 3 do'st taklif qildingiz — 9 000 so'm»);
  hujjat yetkazilganda share tugmasi (eng tabiiy taklif momenti).
- **Manba kuzatuvi**: `/start src_tiktok` kabi deep-linklar → `users.source` ustuni
  (ALTER) — qaysi reklama kanali mijoz olib kelayotganini o'lchash.

### [ ] L. Admin marketing quroli + analitika (`web/admin.py`)

- **Broadcast**: segment tanlab xabar yuborish (hamma / xarid qilganlar / hech qachon
  qilmaganlar / 30 kun faolsiz / balansi borlar). Tezlik 20 msg/sek, blok qilganlarni
  belgilash. Sinov rejimi (avval faqat adminга).
- **Funnel**: start → buyurtma boshladi → to'ladi → yetkazildi (kunlik/haftalik),
  konversiya %, o'rtacha chek, takroriy xarid %, LTV.
- **Baholar hisoboti**: o'rtacha yulduz, past baholi buyurtmalar ro'yxati (sifat signali).
- **Promo samarasi**: qaysi kod nechta buyurtma keltirdi.

### [ ] I. (Doimiy) Sifat kalibrlash

Har 2-3 bosqichdan keyin: bitta to'liq hujjat generatsiya qilib lokalga ko'chir,
foydalanuvchiga ko'rsat, fikr so'ra. So'z soni 90% dan tushib ketsa `_OVERSHOOT`
yoki `chunk_extend` chegarasini qayta sozla.

---

## 4. DEPLOY CHEKLISTI (har bosqichda)

```
1. Lokal: python -m py_compile <fayllar> + lokal smoke-test
2. tar czf /tmp/upd.tar.gz <faqat o'zgargan fayllar>
3. scp -i ~/.ssh/oracle_ssh /tmp/upd.tar.gz opc@141.147.156.65:/tmp/
4. Serverda: _backups/$(date +%Y%m%d_%H%M)/ ga eski nusxa → tar xzf → py_compile
   → import test → (yangi paket bo'lsa .venv/bin/pip install) →
   sudo systemctl restart mustaqilbot → systemctl is-active → journalctl -n 20
5. Jonli sinov (arzon: 10 bet) → natijani o'lchash → /tmp/mustaqilbot/999*.docx tozalash
6. ROADMAP.md da [x] belgilash, xotira faylini yangilash
```

## 5. HOLAT JURNALI

- 2026-07-04 (2): A, B, C, D, F, G, J va K-lite bosqichlari BAJARILDI va deployda:
  titul varag'i (OTM so'raladi), jonli progress, LaTeX→OMML haqiqiy Word tenglamalari,
  web search (adabiyotlar + tahliliy boblar), Premium tarif (opus), 2 bepul revizyon,
  navbat semafori, admin xato-alertlari, retry tugmasi, ⭐ baho + share, welcome-bonus
  5000, cashback 4%, halol ETA. Sinov (10 bet matematika): titul + 2 jadval + 2 grafik
  + 42 OMML tenglama. QOLDI: E (reja tasdiqlash), H (slayd), K-to'liq (promo-kod,
  eslatma joblari, manba deep-link), L (admin broadcast/analitika).
- 2026-07-04: Poydevor tayyor — bo'laklab generatsiya, o'lchab-to'ldirish, jadval/
  grafik (Pillow)/Unicode-formula, fanga xos promptlar, yaroqli API kalit, deploy OK.
  Sinov: 10 bet iqtisod = 4 jadval + 4 grafik; 15 bet = 4073 so'z (~90%).
