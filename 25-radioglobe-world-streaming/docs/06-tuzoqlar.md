# 06 — ⚠️ Texnik tuzoqlar (ENG MUHIM FAYL)

Bu loyihada backend yozish oson. **Qiyin qism — brauzerda begona serverdagi oqimni
ijro etish.** Quyidagi beshta tuzoq arxitekturani belgilagan. Kod yozishdan oldin
shu faylni to'liq o'qish shart.

---

## 1. 🔴 Mixed content — HTTPS sahifa HTTP oqimni yuklay olmaydi

**Muammo:** Saytimiz HTTPS'da. radio-browser'dagi stansiyalarning katta qismi esa
`http://` havolada. Brauzer HTTPS sahifadan HTTP resursni yuklashni **bloklaydi**
(mixed content). Konsolda xato chiqadi, audio ishga tushmaydi.

**Muhim:** bu brauzer xavfsizlik siyosati — kod bilan aylanib o'tib bo'lmaydi.
`<audio>` elementi uchun ham bu amal qiladi.

**Yechim:** **proxy.** Boshqa yo'l yo'q. Bizning serverimiz HTTP orqali oqimni oladi,
HTTPS orqali brauzerga uzatadi.

> Natija: proxy — ixtiyoriy optimizatsiya emas, **majburiy komponent**.

---

## 2. 🔴 CORS — `hls.js` uchun o'limga teng

**Muammo:** Oddiy `<audio src="...">` CORS talab qilmaydi. Lekin:
- HLS oqimlar (`.m3u8`) — `hls.js` manifest va segmentlarni `fetch`/`XHR` bilan oladi
- Demak server `Access-Control-Allow-Origin` header berishi **shart**
- IPTV va ko'p radio serverlari bu headerni **bermaydi**

**Yechim:** proxy header'ni o'zi qo'shadi:
```
Access-Control-Allow-Origin: https://radio.shamsiyev.uz
```

**Nozik nuqta:** Safari HLS'ni nativ qo'llaydi (`<video src="x.m3u8">`) va CORS talab
qilmaydi, Chrome esa `hls.js` orqali talab qiladi. Ya'ni **Safari'da ishlagan oqim
Chrome'da ishlamasligi mumkin.** Test qilishda ikkisini ham ko'rish kerak.

---

## 3. 🔴 SSRF — ochiq proxy serverni o'g'irlab ketadi

Bu eng xavfli tuzoq, va ko'p loyihalar shu yerda xato qiladi.

### ❌ Mutlaqo noto'g'ri yondashuv
```
GET /stream?url=http://begona-server.com/oqim.mp3
```

Nega bu halokat:
1. **SSRF** — kimdir `?url=http://169.254.169.254/latest/meta-data/` yozib, bulut
   serveringizning metadata endpointiga (IAM kalitlarigacha) kirishga harakat qiladi
2. **Ochiq relay** — boshqalar sizning serveringizni o'z trafigi uchun ishlatadi,
   egress xarajati sizga tushadi
3. **Reputatsiya** — serveringiz IP manzili spam/abuse ro'yxatlariga tushadi

### ✅ To'g'ri yondashuv
```
GET /stream/5120?t={imzolangan_token}
```

| Himoya qatlami | Amalga oshirish |
| :--- | :--- |
| URL hech qachon parametrda emas | Faqat `stream_id` → URL bazadan olinadi |
| Faqat tasdiqlangan manzillar | `streams` jadvalida bor bo'lgan URL'lar |
| Imzolangan token | HMAC, 2 soatda tugaydi — havola ulashilmaydi |
| `Origin`/`Referer` tekshiruvi | Hotlinking'dan himoya |
| Private IP blokirovkasi | `10.*`, `172.16-31.*`, `192.168.*`, `127.*`, `169.254.*` — ikkinchi qatlam |
| IP bo'yicha rate limit | Masalan bir IP'dan 3 parallel oqim |
| DNS rebinding himoyasi | URL'ni DB ga yozishdan oldin IP'ni tekshirish, keyin IP bo'yicha ulanish |

---

## 4. 🟠 Bandwidth — yagona o'sadigan xarajat

Proxy degani — **butun trafik sizning serveringiz orqali o'tadi**.

### Radio (MVP)
| Ko'rsatkich | Qiymat |
| :--- | :--- |
| 1 tinglovchi (128 kbps) | ~57 MB/soat |
| 100 parallel tinglovchi | ~12.8 Mbps |
| 100 parallel × 8 soat/kun × 30 kun | **~1.4 TB/oy** |

Bu boshqarilishi mumkin. Serverni tanlashdan oldin egress limitini tekshirish kerak.

### TV (3-bosqich)
| Ko'rsatkich | Qiymat |
| :--- | :--- |
| 1 tomoshabin (3 Mbps) | ~1.35 GB/soat |
| 100 parallel tomoshabin | **~300 Mbps** |

Bu allaqachon jiddiy xarajat. Shuning uchun TV bosqichida:
- HTTPS + CORS beradigan oqimlarni **to'g'ridan-to'g'ri** berish (proxy'siz)
- Faqat majburiy holatda proxy qilish
- HLS segmentlarini qisqa muddat keshlash (bir kanalni N kishi ko'rsa — bitta upstream)

### 2-bosqich optimizatsiyasi: fan-out
Radio uzluksiz oqim bo'lgani uchun keshlanmaydi. Lekin **bir kanalni N kishi tinglasa,
bitta upstream ulanish ochib, N mijozga tarqatish** mumkin (Icecast relay printsipi).

Bu upstream trafikni N barobar kamaytiradi (chiquvchi trafik o'zgarmaydi) va manba
serverlariga hurmat ko'rsatadi. MVP'da 1:1 passthrough yetarli — optimizatsiyani
muammo paydo bo'lganda qilish kerak.

---

## 5. 🟠 Globus SEO'ga qarshi

**Muammo:** WebGL canvas Google uchun bo'sh sahifa. Next.js'ni SEO uchun tanlab, keyin
butun navigatsiyani canvas ichiga yashirish — ikki qarorning bir-birini yo'q qilishi.

**Yechim (to'rt qatlam):**
1. Globus ostida **haqiqiy `<a href>` havolalar** ro'yxati (SSR'da)
2. SEO kontenti alohida SSR sahifalarda (`/radio/[country]`), JSON-LD bilan
3. Globus `ssr: false` + lazy — LCP elementi **matn** bo'lishi kerak, canvas emas
4. WebGL fallback (ro'yxat) — u ham SEO versiyasi vazifasini bajaradi

Batafsil: [`04-frontend.md`](./04-frontend.md) → 2-bo'lim.

---

## 6. 🟡 Pleyer navigatsiyada to'xtaydi

**Muammo:** React'da oddiy yondashuvda sahifa o'zgarganda komponent unmount bo'ladi,
`<audio>` DOM'dan chiqadi, musiqa to'xtaydi. Foydalanuvchi boshqa davlatni ko'rmoqchi
bo'lsa — tinglayotgan radiosi uziladi.

**Yechim:** `<audio>` root layoutda, holat Zustand'da. Qarang:
[`04-frontend.md`](./04-frontend.md) → 3-bo'lim.

**Buni keyin tuzatish — og'riqli refactor.** Boshidan to'g'ri qurish kerak.

---

## 7. 🟡 O'lik havolalar — mahsulotni o'ldiradigan muammo

**Muammo:** Radio/TV kataloglarida havolalar doimiy o'ladi. Agar foydalanuvchi uch marta
bosib hech biri ishlamasa — u saytga **qaytmaydi**. Bu texnik emas, mahsulot muammosi.

**Yechim (uch qatlam):**
1. **Health checker** — oqimlarni muntazam tekshiradi, `score` qo'yadi
   ([`01-arxitektura.md`](./01-arxitektura.md) → 5-bo'lim)
2. **API filtri** — `score > 20` bo'lmagan oqimlar ro'yxatga umuman chiqmaydi
3. **Frontend fallback** — birinchi oqim ishlamasa, zaxira oqimlarga avtomatik o'tadi;
   xato faqat barchasi tugaganda ko'rsatiladi

**Asosiy metrika:** `ijro boshlangan / bosilgan` nisbati. Bu raqam 90% dan pastga
tushsa — katalog buzilgan.

---

## 8. 🟡 Brauzer audio tuzoqlari

| Tuzoq | Yechim |
| :--- | :--- |
| Mobil autoplay policy | Ijro faqat `click` hodisasi ichida boshlanishi kerak |
| Oqim "qotib" qoladi, `error` bermaydi | `stalled`/`waiting` hodisasiga 30s timeout |
| HLS radiolar ham bor | `hls.js` radio uchun ham kerak, faqat TV emas |
| Lock-screen boshqaruvi yo'q | `MediaSession API` — nom, logo, play/pause |
| iOS Safari ovoz balandligini kodda o'zgartirmaydi | Faqat qurilma tugmalari bilan — UI'da hisobga olish |
| ICY metadata ("hozir ijroda") brauzerda o'qilmaydi | Proxy o'qiydi → SSE orqali frontendga (2-bosqich) |

---

## 9. 🟡 Xarita ma'lumotlari tuzog'i: `ISO_A2 = -99`

Natural Earth GeoJSON'da ba'zi davlatlarda `ISO_A2` maydoni `-99` bo'lib chiqadi.
`iso2` bo'yicha bog'lasak — o'sha davlatlar bosilmaydi, va sababi darhol ko'rinmaydi.

**Yechim:** raqamli **M49 kodi** bo'yicha bog'lanish. Qarang:
[`02-malumotlar-modeli.md`](./02-malumotlar-modeli.md) → 1-bo'lim.

---

## 10. 🟢 `stream_checks` jadvali bazani bo'g'ib qo'yadi

50 000 oqim × kuniga ~10 tekshiruv = **oyiga 15 million qator**. Partitioning bo'lmasa
6 oyda muammo boshlanadi.

**Yechim:** `checked_at` bo'yicha oylik `RANGE` partition, 3 oydan keyin
`DROP PARTITION`. Qarang: [`02-malumotlar-modeli.md`](./02-malumotlar-modeli.md) → 5-bo'lim.

---

## Xulosa — ustuvorlik tartibi

| # | Tuzoq | Daraja | Hal qilinishi |
| :-- | :--- | :--- | :--- |
| 1 | Mixed content (HTTP oqim) | 🔴 Blokirovchi | Proxy — majburiy komponent |
| 2 | CORS (hls.js) | 🔴 Blokirovchi | Proxy header qo'shadi |
| 3 | SSRF / ochiq relay | 🔴 Xavfsizlik | `stream_id` + imzolangan token |
| 4 | Bandwidth xarajati | 🟠 Iqtisodiy | Radiodan boshlash, fan-out keyin |
| 5 | Globus vs SEO | 🟠 Mahsulot | SSR havolalar + fallback |
| 6 | Pleyer unmount | 🟡 Arxitektura | Root layout + Zustand |
| 7 | O'lik havolalar | 🟡 Mahsulot | Health checker + API filtri |
| 8 | Brauzer audio | 🟡 Amaliy | Timeout, MediaSession, hls.js |
| 9 | `ISO_A2 = -99` | 🟡 Ma'lumot | M49 bo'yicha bog'lash |
| 10 | `stream_checks` o'sishi | 🟢 Kelgusi | Partitioning |
