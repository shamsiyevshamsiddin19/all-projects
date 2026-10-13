# 05 — Kontent manbalari va ingest

## 1. Asosiy haqiqat

Loyihaning muvaffaqiyati kod sifatiga emas, **katalog sifatiga** bog'liq. Shuning uchun
manbalarni to'g'ri tanlash — birinchi darajali qaror.

| Tur | Manba | Hajm | Sifat | Huquqiy holat |
| :--- | :--- | :--- | :--- | :--- |
| 🎙 Radio | **radio-browser.info** | ~50 000 stansiya | ✅ Yaxshi | ✅ Toza — ochiq, jamoatchilik bazasi |
| 📺 TV | **iptv-org** | ~10 000 kanal | ⚠️ Past — ko'pi o'lik/geo-bloklangan | ⚠️ Ehtiyot talab qiladi |

**Shuning uchun MVP faqat radio.** Radio tomoni arzon, legal toza va darhol foydali
mahsulot beradi. TV — alohida bosqich, alohida ehtiyotkorlik.

---

## 2. radio-browser.info (asosiy manba)

Ochiq, bepul, jamoatchilik tomonidan to'ldiriladigan radiostansiyalar bazasi. API ochiq,
kalit kerak emas.

### Bergan ma'lumotlari (bizga kerakli maydonlar)

| Maydon | Bizda qayerga tushadi |
| :--- | :--- |
| `stationuuid` | `channels.external_ids.radiobrowser_uuid` |
| `name` | `channels.name` |
| `url` / `url_resolved` | `streams.url` / `streams.url_resolved` |
| `countrycode` (ISO2) | `channel_countries.country_iso2` |
| `favicon` | `channels.logo_url` |
| `tags` | `channels.tags` |
| `language` / `languagecodes` | `channels.languages` |
| `codec` / `bitrate` | `streams.kind` / `streams.bitrate` |
| `geo_lat` / `geo_long` | globusda nuqta ko'rsatish (keyinroq) |
| `votes` / `clickcount` | boshlang'ich `popularity` |

### Ishlatish qoidalari (muhim)
- **Mirror DNS:** `all.api.radio-browser.info` — DNS round-robin bilan bir nechta
  serverga taqsimlaydi. Bitta serverga qadalib qolmaslik kerak.
- **`User-Agent` majburiy** — o'z ilova nomingizni yuborish shart
  (masalan `RadioGlobe/1.0 (+https://radio.shamsiyev.uz)`). Aks holda bloklanadi.
- **Sinxronizatsiya chastotasi:** kunda 1 marta yetarli. Soatlab tortish — suiiste'mol.
- **Inkremental sinxronizatsiya imkoniyati bor** — oxirgi o'zgarish bo'yicha filtrlash.
  Aniq endpoint nomini ingest yozilishidan oldin ularning hujjatidan tekshirish kerak.

### ⭐ Eng foydali detal: klik qaytarish
Stansiya ijro etilganda radio-browser'ning klik endpointini
(`/json/url/{stationuuid}` ko'rinishidagi) chaqirish kerak. Bu:

1. **Jamiyatga hurmat** — ularning reyting tizimi bizning ma'lumotimiz bilan boyitiladi
2. **Bizga foyda** — javobda **ishlaydigan `url_resolved`** qaytadi, ya'ni redirect
   zanjirini o'zimiz kuzatishimiz kerak emas

Shuning uchun bizning `POST /api/v1/play` endpointi tabiiy ravishda shu chaqiruvni
o'z ichiga oladi. Ikki ish bitta joyda.

---

## 3. iptv-org (TV — 3-bosqich)

Ommaviy ravishda e'lon qilingan IPTV havolalarining ochiq katalogi. M3U pleylistlar
davlatlar bo'yicha guruhlangan, bundan tashqari JSON API bor (`channels`, `streams`,
`countries`, `categories`, `logos`).

### Kutilayotgan muammolar
| Muammo | Ko'lami |
| :--- | :--- |
| O'lik havolalar | Juda ko'p — health checker majburiy |
| Geo-bloklash | Ko'p kanal faqat o'z davlatidan ishlaydi |
| CORS header yo'qligi | Deyarli hamma joyda → proxy majburiy |
| Yuqori bandwidth | 2–5 Mbps/tomoshabin (radiodan ~30 barobar ko'p) |

### Natija
TV'ni qo'shishdan oldin health checker allaqachon ishlab turgan bo'lishi kerak. Aks
holda sayt "bosdim — ishlamadi" tajribasiga aylanadi va foydalanuvchi qaytmaydi.

---

## 4. Xarita geometriyasi

**Manba:** `world-atlas` (`countries-110m.json`, TopoJSON) — Natural Earth asosida.

**Jarayon:**
```
countries-110m.json (TopoJSON)
   │ topojson-client bilan GeoJSON ga
   ▼
GeoJSON (raqamli M49 id bilan)
   │ mapshaper bilan soddalashtirish
   │ DB dan iso2/slug/nom/kanal_soni qo'shish
   ▼
countries.geojson (~80–120 KB, brotli bilan)
```

### ⚠️ Nozik nuqta: `ISO_A2 = -99`
Natural Earth ma'lumotlarida ba'zi davlatlarda `ISO_A2` maydoni `-99` bo'lib chiqadi
(Fransiya, Norvegiya, Kosovo va boshqalar — versiyaga qarab). Agar xaritani `iso2`
bo'yicha bog'lasak, bu davlatlar bosilmaydigan bo'lib qoladi va sababini topish qiyin.

**Yechim:** bog'lanish **raqamli M49 kodi** bo'yicha (`countries.m49`), `iso2` esa faqat
URL va biznes-mantiq uchun. Qarang: [`02-malumotlar-modeli.md`](./02-malumotlar-modeli.md).

---

## 5. Ingest arxitekturasi

```
Worker (kunlik cron)
  │
  ├─ 1. sources.last_sync_at ni o'qish
  ├─ 2. radio-browser'dan ma'lumot tortish (User-Agent bilan, mirror orqali)
  ├─ 3. Normalizatsiya:
  │      ├─ davlat kodini countries.iso2 ga moslash (noto'g'rilarini chetga)
  │      ├─ nomni tozalash (ortiqcha bo'shliq, emoji, "LIVE" kabi shovqin)
  │      ├─ slug generatsiya (takrorlansa -2, -3 qo'shiladi)
  │      └─ tag/tilni lug'at bo'yicha normallashtirish
  ├─ 4. UPSERT: external_ids.radiobrowser_uuid bo'yicha
  ├─ 5. Manbadan yo'qolgan stansiyalarni is_archived = TRUE qilish (O'CHIRMASLIK)
  ├─ 6. countries.radio_count ni qayta hisoblash
  └─ 7. sources.last_sync_at / last_sync_ok ni yozish
```

### ⚠️ Nozik nuqta: hech narsa o'chirilmaydi
Manbadan stansiya yo'qolsa — biz uni **o'chirmaymiz**, `is_archived = TRUE` qilamiz.
Sabab: manbada vaqtinchalik xato bo'lishi mumkin, va o'chirilgan ma'lumot bilan birga
bizning statistikamiz, slug'larimiz va tashqi havolalarimiz ham yo'qoladi.

---

## 6. Huquqiy jihat

Bu loyihada **kontent saqlanmaydi** — faqat ommaviy e'lon qilingan havolalar katalogi.
Shunga qaramay quyidagilar boshidan bajarilishi kerak:

| Talab | Amalga oshirish |
| :--- | :--- |
| Faqat ommaviy/rasmiy oqimlar | Manbalar ro'yxati hujjatlashtirilgan va tekshiriladigan |
| Kontentni qayta tarqatmaslik | Biz saqlamaymiz, faqat proxy qilamiz (HTTPS/CORS uchun) |
| Shikoyat (takedown) kanali | `/dmca` sahifasi + email, 48 soatda javob |
| Geo-cheklovlarni hurmat qilish | Geo-bloklangan oqimlar yashiriladi, aylanib o'tilmaydi |
| Manbaga havola | Har stansiya sahifasida uning rasmiy saytiga havola |
| `robots.txt` va cheklovlar | Oqim URL'lari indekslanmaydi |

**Alohida eslatma:** proxy faqat HTTPS/CORS muammosini hal qilish uchun, kontentni
"ochish" yoki geo-blokni aylanib o'tish uchun emas. Geo-bloklangan oqimni proxy orqali
berish — texnik jihatdan mumkin, lekin bu yo'l tanlanmaydi.
