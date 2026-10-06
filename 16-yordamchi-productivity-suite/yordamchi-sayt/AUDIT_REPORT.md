# 🔍 YORDAMCHI TIZIMI — TO'LIQ AUDIT VA CHUQUR TADQIQOT HISOBOTI (DEEP RESEARCH REPORT)

> **Sana:** 2026-yil 10-sentyabr  
> **Loyiha:** Yordamchi Sayt (PWA + Vanilla JS SPA + FastAPI / PostgreSQL Backend)  
> **Tekshiruv qamrovi:** Frontend (`assets/js/`, `assets/css/`, `index.html`, `service-worker.js`), Backend (`backend_py/`), Baza (`database/`), Deploy skriptlari (`deploy.sh`), Oflayn kesh va Xavfsizlik.  
> **Jami tekshirilgan fayllar:** 46 ta frontend JS moduli, 2 ta asosiy CSS fayli, 21 ta backend Python moduli, SQL sxemalari va Service Worker.

---

## 📑 MUNDARIJA
1. [Xulosa va Umumiy Holat (Executive Summary)](#1-xulosa-va-umumiy-holat)
2. [Xatolar Darajalanish Matritsasi (Severity Matrix)](#2-xatolar-darajalanish-matritsasi)
3. [🔴 KRITIK XATOLAR (Critical Bugs)](#3--kritik-xatolar)
4. [🟠 YUQORI DARAJADAGI XATOLAR (High Severity)](#4--yuqori-darajadagi-xatolar)
5. [🟡 MANTIQIY VA FUNKSIONAL KAMCHILIKLAR (Medium Severity)](#5--mantiqiy-va-funksional-kamchiliklar)
6. [🔵 UX, MOBIL VA DIZAYN MOSLASHUVI NUQSONLARI (Low / UX)](#6--ux-mobil-va-dizayn-moslashuvi-nuqsonlari)
7. [⚙️ DEPLOY VA INFRATUZILMA KAMCHILIKLARI](#7-deploy-va-infratuzilma-kamchiliklari)
8. [🚀 AMALGA OSHIRISH VA TUZATISH REJASI (Actionable Roadmap)](#8-amalga-oshirish-va-tuzatish-rejasi)

---

## 1. Xulosa va Umumiy Holat

Loyiha arxitekturasi juda yaxshi o'ylangan — tashqi og'ir freymvorklarsiz (React, Vue, Tailwind'siz) yozilgan sof Vanilla JS arxitekturasi, tezkor SPA marshrutlash, oflayn rejim uchun mukammal Service Worker va Stale-While-Revalidate kesh strategiyasi mavjud. Unit testlar tizimi (458 ta test) barcha asosiy hisoblash mantiqlarini qamrab olgan.

Biroq, chuqur tahlil (Deep Research) natijasida quyidagi yo'nalishlarda nosozliklar, mantiqiy chalkashliklar va yashirin nuqsonlar aniqlandi:
- **Resurslar va Kesh:** Mavjud bo'lmagan faylga murojaat tufayli PWA Service Worker o'rnatilishida 404 xatosi.
- **Xotira va CPU:** Kirish (Auth) oynasi yopilgandan keyin ham orqa fonda to'xtovsiz aylanib turuvchi 60/120 FPS cheksiz loop.
- **Audio/TTS:** Brauzer audioplatformasidagi uzilishlar paytida ovoz chiqarish mexanizmining abadiy qotib qolishi.
- **Xavfsizlik va Ruxsatlar:** "Admin" paroli bilan kirilganda administratorlik huquqlarining yo'qolib, oddiy foydalanuvchiga aylanib qolishi.
- **Storage Kvotasi:** LocalStorage'ga katta hajmdagi Base64 rasmlarni try-catch'siz yozish va xotira chegarasidan oshib ketish xavfi.
- **Ma'lumotlar Inconsistentligi:** Bosh sahifadagi kartochka va haqiqiy ma'lumotlar bazasi o'rtasidagi son nomutanosibligi (210 vs 229).

---

## 2. Xatolar Darajalanish Matritsasi

| ID | Toifa | Fayl va Joylashuv | Tavsif | Darajasi |
|---|---|---|---|---|
| **K-01** | Resurs / SW | `index.html:82` | `app-icon-192.png` 404 xatosi va Service Worker precache buzilishi | 🔴 Kritik |
| **K-02** | CPU / Performance | `assets/js/app2/auth.js:359` | Auth yopilgach to'xtamaydigan `requestAnimationFrame` loopi | 🔴 Kritik |
| **K-03** | Audio / Logic | `assets/js/core/tts.js:253` | Audio xatosida TTS callback'ning chaqirilmay qotib qolishi | 🔴 Kritik |
| **Y-01** | Storage / Safari | `assets/js/app2/settings.js:140` | Base64 rasmlarni LocalStorage'ga nazoratsiz saqlash va kvota to'lishi | 🟠 Yuqori |
| **Y-02** | Backend / Auth | `backend_py/app/handlers/auth.py:110` | "admin" emailida kirilganda adminlik rolining yo'qolishi (403 xatosi) | 🟠 Yuqori |
| **M-01** | Kontent / UI | `assets/js/app2/home.js:20` | Bosh sahifa Stories'da 210 ta fe'l yozilgan, bazada esa 229 ta | 🟡 O'rta |
| **M-02** | Disk / Bandwidth | `assets/video/losnhaazpv.mp4` | 5.1 MB o'lik (ishlatilmaydigan) video fayl mavjudligi | 🟡 O'rta |
| **M-03** | Deploy / URL | `assets/js/app2/auth.js:99` | Fon videosi uchun mutlaq yo'l (`/assets/...`) berilgani | 🟡 O'rta |
| **M-04** | Parser / Markdown | `assets/js/app2/core.js:880` | `safeUrl` nisbiy rasm yo'llarini bloklab qo'yishi | 🟡 O'rta |
| **M-05** | Offline / PWA | `assets/js/app2/vocab.js:951` | MD lug'at kitoblari Service Worker precache'da yo'qligi | 🟡 O'rta |
| **M-06** | Logic / Filter | `assets/js/app2/habits.js:111` | Odatlar ro'yxatida noma'lum rejimli odatlar ko'rinmay qolishi | 🟡 O'rta |
| **M-07** | UX / Edge Case | `assets/js/app2/vocab.js:2485` | Oraliq va filtr bo'sh kelganda tozalash tugmasining yo'qligi | 🟡 O'rta |
| **M-08** | Offline / CDN | `assets/js/app2/quiz.js:39` | MathJax tashqi CDN ga bog'langan, oflaynda ishlamaydi | 🟡 O'rta |
| **U-01** | CSS / iOS | `assets/css/app.css:5009` | `100vh` sababli Mobil Safari'da panel tugmalari pastda yopilib qolishi | 🔵 Quyi |
| **U-02** | HTML / Head | `index.html:18,24` | `<link rel="icon">` teglarida boshlang'ich `href` atributi yo'qligi | 🔵 Quyi |
| **U-03** | CI / Deploy | `deploy.sh:40` | `--all-changed` rejimi faqat `.js` va `.css` fayllarni ko'rishi | 🔵 Quyi |

---

## 3. 🔴 KRITIK XATOLAR

### [K-01] Mavjud bo'lmagan rasm (404) va Service Worker Precache barbod bo'lishi

- **Fayl:** `index.html` (82-qator)
- **Kod:**
  ```html
  <img id="side-logo" class="side-brand-img" data-app-icon alt="" src="assets/icons/app-icon-192.png">
  ```
- **Ildiz sababi (Root Cause):**
  Loyiha papkasida `assets/icons/app-icon-192.png` nomli fayl umuman mavjud emas! Mavjud fayllar: `custom-app-icon-192.png`, `custom-app-icon-512.png`, `app-icon.png` va `app-logo.svg`.
- **Ta'siri:**
  1. Har bir sahifa yangilanganda brauzer konsolida qizil `GET https://.../assets/icons/app-icon-192.png 404 (Not Found)` chiqadi.
  2. `service-worker.js` fayli `shellUrls()` funksiyasida `index.html` ichidagi barcha `src="..."` larni o'qiydi va keshga oldindan yuklashga (precache) qo'yadi. Natijada Service Worker o'rnatilish vaqtida ushbu 404 faylni yuklay olmaydi, ikki marta urinib ham xatolik qaytaradi.
- **Tavsiya etilgan yechim:**
  `index.html` 82-qatordagi manzilni to'g'ri mavjud faylga almashtirish:
  ```html
  <img id="side-logo" class="side-brand-img" data-app-icon alt="" src="assets/icons/custom-app-icon-192.png">
  ```

---

### [K-02] Auth oynasi yopilgach to'xtamaydigan abadiy `requestAnimationFrame` loopi

- **Fayl:** `assets/js/app2/auth.js` (359–401 qatorlar)
- **Kod:**
  ```javascript
  (function initSeamlessVideo() {
    var v1 = el.querySelector('#au-art-vid-1');
    var v2 = el.querySelector('#au-art-vid-2');
    if (!v1 || !v2) return;
    ...
    function checkLoop() {
      if (active && active.duration && !isFading) {
        ...
      }
      requestAnimationFrame(checkLoop); // <-- TO'XTASH SHARTI YO'Q!
    }
    requestAnimationFrame(checkLoop);
  })();
  ```
- **Ildiz sababi:**
  Foydalanuvchi muvaffaqiyatli kirgach (Google yoki parol orqali), `closeScreen()` chaqirilib `#auth-screen` elementi DOM'dan butunlay o'chiriladi (`el.remove()`). Biroq `checkLoop()` hech qanday to'xtash tekshiruviga ega emas! U xotiradagi `v1` va `v2` o'zgaruvchilarini ushlab qoladi va cheksiz ravishda har bir freymda (soniyasiga 60 yoki 120 marta) `requestAnimationFrame` orqali o'zini chaqiraveradi.
- **Ta'siri:**
  Foydalanuvchi tizimga kirganidan so'ng butun sessiya davomida fonda bo'sh CPU va render loop ishlaydi. Noutbuk va telefonlarda batareya qiziydi va quvvat tez tugaydi.
- **Tavsiya etilgan yechim:**
  Loop boshida element DOM'da mavjudligini tekshirish va yo'q bo'lsa loopni to'xtatish:
  ```javascript
  function checkLoop() {
    if (!document.body.contains(el)) return; // Agar ekran yopilgan bo'lsa darhol to'xtaydi!
    ...
    requestAnimationFrame(checkLoop);
  }
  ```

---

### [K-03] Brauzer audio uzilishida TTS callback'ning chaqirilmay abadiy qotib qolishi

- **Fayl:** `assets/js/core/tts.js` (253–259 qatorlar)
- **Kod:**
  ```javascript
  u.onerror = function (e) {
    /* `interrupted`/`canceled` — bu BIZ to'xtatganmiz, xato emas. */
    var err = e && e.error;
    stopKeepAlive();
    if (myGen !== state.gen || err === 'interrupted' || err === 'canceled') return;
    fire(new Error(err || 'tts-error'));
  };
  ```
- **Ildiz sababi:**
  Agar biz o'zimiz `cancel()` ni chaqirsak, `state.gen++` oshadi. Lekin agar mobil telefonda qo'ng'iroq kelsa, bildirishnoma ovozi chiqsa yoki brauzer audio fokusni yo'qotib avtomatik ravishda nutqni uzsa (`err === 'interrupted'` yoki `err === 'canceled'`), `myGen === state.gen` bo'lishiga qaramay funksiya `return` qilib ketadi! Hech qanday `fire()` (na `fire(null)` va na `fire(err)`) chaqirilmaydi!
- **Ta'siri:**
  `reading.js`, `listening-doc.js` kabi o'qituvchi modullarda:
  ```javascript
  App.TTS.speak(text, opts, function(err) {
    setSpeaking(false);
    nextSentence();
  });
  ```
  Callback hech qachon chaqirilmagani sababli ekran "O'qilmoqda..." holatida abadiy qotib qoladi, keyingi gapga o'tmaydi va qayta boshlash imkonsiz bo'lib qoladi.
- **Tavsiya etilgan yechim:**
  Agar generatsiya o'zgarmagan bo'lsa (`myGen === state.gen`), xato `interrupted` bo'lsa ham chaqiruvchiga jarayon tugaganligini bildirish (`fire(null)`):
  ```javascript
  u.onerror = function (e) {
    var err = e && e.error;
    stopKeepAlive();
    if (myGen !== state.gen) return;
    if (err === 'interrupted' || err === 'canceled') {
      fire(null); // Jarayon uzildi, lekin kutayotgan modulni ozod qilamiz
      return;
    }
    fire(new Error(err || 'tts-error'));
  };
  ```

---

## 4. 🟠 YUQORI DARAJADAGI XATOLAR

### [Y-01] LocalStorage kvotasi oshib ketishi va `try/catch`siz saqlash

- **Fayllar:** `assets/js/app2/settings.js` (140, 174, 177-qatorlar), `assets/js/core/remote-storage.js` (557-qator).
- **Muammo:**
  Foydalanuvchi profil rasmini (`user_avatar`) yoki ilova belgisini (`app_custom_icon`, `app_custom_icon_192`) o'zgartirganda, Base64 formatidagi katta hajmli ma'lumotlar `localStorage.setItem(...)` orqali saqlanadi.
  ```javascript
  resizeImage(f, 512, function (data) {
    localStorage.setItem('app_custom_icon', data); // <-- TRY/CATCH YO'Q!
  ```
  Bundan tashqari, `remote-storage.js` drayveri LocalStorage'dagi har bir yozuvni ushlab oladi va `__app_storage_snapshot_v1__` ichiga yana bir marta to'liq nusxasini yozadi.
- **Ta'siri:**
  Ayniqsa Safari brauzerida (iOS Safari standart 5MB qat'iy limitga ega) yoki Private Browsing rejimida `QuotaExceededError` vujudga keladi. Xatolik tutilmagani sababli butun JS skriptining bajarilishi to'xtaydi (crash).
- **Tavsiya etilgan yechim:**
  1. Barcha rasm saqlash joylariga `try { ... } catch (e) { App.toast("⚠️ Xotirada joy yetarli emas"); }` o'rnatish.
  2. Rasm o'lchamlarini optimallashtirish (masalan, 512px o'rniga 256px va WebP/JPEG siqish koeffitsienti 0.75).
  3. Katta hajmli binar/base64 ma'lumotlarni (`app_custom_icon`, `user_avatar`) `remote-storage` ning umumiy sinxronizatsiya snapshot'iga kiritmaslik (ularni alohida IndexedDB yoki istisno kalit sifatida saqlash).

---

### [Y-02] Parol bilan kirilganda "admin" foydalanuvchisining ruxsatsizlanib qolishi

- **Fayllar:** `backend_py/app/handlers/auth.py` (110–139-qatorlar), `backend_py/app/handlers/users.py` (31–36-qatorlar).
- **Muammo:**
  Foydalanuvchi `kirish` amali orqali (email: "admin", parol: "...") kirganda:
  ```python
  request.session["doktor_id"] = int(doktor["id"])
  request.session["doktor_ism"] = doktor["ism"]
  request.session["doktor_email"] = doktor["email"]
  # request.session["role"] BELGILANMAGAN!
  ```
  Sessiyada `role` bo'sh qoladi. Keyingi so'rovlarda `_require_admin()` tekshiruvi ishga tushadi:
  ```python
  def _require_admin(request: Request) -> None:
      role = request.session.get("role")
      email = (request.session.get("doktor_email") or "").strip().lower()
      if role == "admin" or (email and email in settings.ALLOWED_EMAILS):
          return
      raise ApiError("Faqat administrator uchun ruxsat berilgan.", 403)
  ```
  `settings.ALLOWED_EMAILS` ro'yxatida faqat Google orqali kiruvchi haqiqiy email manzillar (`shamsiddin...`) yozilgan, "admin" so'zi yo'q.
- **Ta'siri:**
  Asosiy admin foydalanuvchisi o'z paroli bilan tizimga kirganida, u tizimda oddiy "user" sifatida ko'riladi. Foydalanuvchilarni boshqarish (`users_list`, `user_add`, `user_update`) kabi admin amallari 403 Forbidden xatosini qaytaradi.
- **Tavsiya etilgan yechim:**
  `auth.py` dagi `_login` funksiyasida kirgan foydalanuvchi admin ekanligini to'g'ri tekshirib, sessiyaga `role` va `ruxsatlar`ni belgilash:
  ```python
  is_admin = is_admin_email(doktor["email"]) or doktor["email"].lower() == "admin"
  request.session["role"] = "admin" if is_admin else "user"
  request.session["ruxsatlar"] = ["*"] if is_admin else ["home", "languages", "fanlar", "stats"]
  ```

---

## 5. 🟡 MANTIQIY VA FUNKSIONAL KAMCHILIKLAR

### [M-01] Bosh sahifa Stories'da "210 ta fe'l" deb qolib ketgani (Aslida 229 ta)

- **Fayl:** `assets/js/app2/home.js` (19–27 qatorlar)
- **Muammo:**
  ```javascript
  {
    id: 'ru_229',
    title: '210 ta fe\'l',
    sub: 'Hozirgi zamon',
    badge: '210',
    desc: 'Rus tilida eng ko\'p ishlatiladigan 210 ta fe\'lning...',
  ```
  Bazada, lug'at bo'limida va `assets/md_books/229_ta_fel_MUKAMMAL.md` faylida ushbu ro'yxat **229 taga** yetkazilgan va to'ldirilgan. Stories qismida esa eski `210` soni o'zgarmay qolgan.
- **Tuzatish:**
  `title: "229 ta fe'l"`, `badge: "229"`, `desc: "...229 ta fe'lning..."` ga yangilash.

---

### [M-02] 5.1 MB hajmdagi ishlatilmaydigan (o'lik) video fayl

- **Fayl:** `assets/video/losnhaazpv.mp4` (Hajmi: 5.1 Megabayt)
- **Muammo:**
  Loyiha bo'ylab qidirilganda ushbu videoga hech qanday havola yo'q. Kirish ekranida faqat 282 KB hajmli `omyznfqvll.mp4` ishlatiladi.
- **Tuzatish:**
  `assets/video/losnhaazpv.mp4` faylini repositoriyadan va serverdan o'chirish. Bu sayt deployini sezilarli darajada tezlashtiradi.

---

### [M-03] Kirish fon videosida mutlaq yo'l (`/assets/...`) berilgani

- **Fayl:** `assets/js/app2/auth.js` (99 va 100-qatorlar)
- **Muammo:**
  ```javascript
  '<video id="au-art-vid-1" ... src="/assets/video/omyznfqvll.mp4"></video>'
  ```
  Saytning barcha boshqa joylarida nisbiy yo'l (`assets/...` yoki `./assets/...`) ishlatilgan. Boshidagi `/` belgisi sayt domening ildizida bo'lmagan holatlarda (masalan, subfolder yoki lokal WebView) 404 xatosiga olib keladi.
- **Tuzatish:**
  `src="assets/video/omyznfqvll.mp4"` ko'rinishiga keltirish.

---

### [M-04] Markdown parserda nisbiy rasm manzillarining o'chib ketishi

- **Fayl:** `assets/js/app2/core.js` (880–883 qatorlar)
- **Muammo:**
  ```javascript
  function safeUrl(u) {
    var s = String(u || '').trim();
    if (/^(https?:|mailto:|tel:|\/|#|data:image\/)/i.test(s)) return s;
    return '';
  }
  ```
  Agar darslik yoki qoidalar ichidagi markdown matnida `![Sxema](assets/img/sxema.png)` yoki `./assets/...` yozilsa, `safeUrl` bo'sh satr qaytaradi va foydalanuvchiga rasm o'rniga faqat `Sxema` degan matn chiqadi.
- **Tuzatish:**
  `safeUrl` regexiga nisbiy yo'llar va rasm kengaytmalarini kiritish:
  ```javascript
  if (/^(https?:|mailto:|tel:|\/|\.\/|#|data:image\/|[a-zA-Z0-9_\-\.\/]+\.(png|jpe?g|gif|svg|webp))/i.test(s) && !/^\s*javascript:/i.test(s)) return s;
  ```

---

### [M-05] MD Lug'at kitoblarining oflayn keshlanmasligi

- **Fayllar:** `assets/js/app2/vocab.js` (950–975 qatorlar), `service-worker.js`.
- **Muammo:**
  `SYSTEM_MD_BOOKS` dagi 6 ta asosiy kitob (`assets/md_books/*.md`) dinamik `fetch()` bilan tortib olinadi. Lekin ular `service-worker.js` ning precache ro'yxatida yo'q.
- **Ta'siri:**
  Agar foydalanuvchi ilovani o'rnatib olib, biror marta kitobni ochmagan holda oflayn qolsa, keyinchalik ushbu kitoblarni ochib o'qiy olmaydi.
- **Tuzatish:**
  `service-worker.js` faylining `shellUrls()` ro'yxatiga ushbu 6 ta kitob yo'lini ham qo'shib qo'yish:
  ```javascript
  './assets/md_books/229_ta_fel_MUKAMMAL.md',
  './assets/md_books/Rus_tili_1000_soz_MUKAMMAL.md',
  './assets/md_books/Rus_tili_8000_soz_TARJIMA.md',
  ...
  ```

---

### [M-06] Odatlar (Habits) ro'yxatida noma'lum rejimli odatlar ko'rinmay qolishi

- **Fayl:** `assets/js/app2/habits.js` (111–129 qatorlar)
- **Muammo:**
  ```javascript
  MODE_ORDER.forEach(function (m) {
    var group = list.filter(function (x) { return x.week_mode === m; });
  ```
  `MODE_ORDER` qat'iy ravishda 5 ta qiymatdan iborat: `['everyday', 'odd', 'even', 'weekday', 'weekend']`. Agar ma'lumotlar bazasida biror odatning `week_mode` qiymati bo'sh, `null` yoki boshqa qiymat bo'lsa, u ro'yxatda umuman ko'rinmaydi.
- **Tuzatish:**
  Ushbu 5 toifaga kirmagan qolgan odatlarni "Boshqa" (yoki "Har kuni" ga tenglashtirib) chiqarish.

---

### [M-07] Lug'atda oraliq va filtr birgalikda bo'sh kelganda yechim tugmasi yo'qligi

- **Fayl:** `assets/js/app2/vocab.js` (2485–2505 qatorlar)
- **Muammo:**
  Agar foydalanuvchi 100–150 oralig'ini tanlab, filtrdan "Qiyin"ni bossa va bu oraliqda qiyin so'z bo'lmasa, `displayRows` bo'sh qoladi. Ekranda "Bu oraliqda so'z yo'q" yozuvi chiqadi, ammo oraliqni yoki filtrni tozalash uchun qulay tugma taqdim etilmaydi.
- **Tuzatish:**
  Bo'sh holat (`App.empty`) ichiga "Filtrni tozalash" yoki "Oraliqni tozalash" tugmasini kiritish.

---

### [M-08] MathJax tashqi CDN ga bog'langan (Oflaynda formulalar buziladi)

- **Fayl:** `assets/js/app2/quiz.js` (39-qator)
- **Muammo:**
  Formula chizish uchun har safar `https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js` tashqi manzilidan yuklanadi.
- **Ta'siri:**
  Internet bo'lmaganda testlar ichidagi matematik va fizik formulalar chiroyli render bo'lmay, xom `\( ... \)` ko'rinishida qolib ketadi.
- **Tuzatish:**
  Kerakli yengil formula chizish kutubxonasini lokal `assets/js/vendor/` ga joylash yoki Service Worker orqali keshlab qo'yish.

---

## 6. 🔵 UX, MOBIL VA DIZAYN MOSLASHUVI NUQSONLARI

### [U-01] Mobil Safari'da `100vh` sababli pastki tugmalarning yashirinib qolishi

- **Fayl:** `assets/css/app.css` (5009 va 5034-qatorlar)
- **Muammo:**
  `.sheet.vd-side-panel` uchun `height: 100vh !important; max-height: 100vh !important;` belgilangan.
  Mobil iOS Safari'da pastki manzil satri (URL bar) ochiq turganda `100vh` ekranning pastki qismini qoplaydi va yon panelning pastki tugmalari bar ostida qolib, bosish noqulay bo'ladi.
- **Tuzatish:**
  Zamonaviy `dvh` (Dynamic Viewport Height) o'lchamini qo'llash:
  ```css
  height: 100vh !important;
  height: 100dvh !important;
  max-height: 100dvh !important;
  ```

---

### [U-02] `<link rel="icon">` teglarida boshlang'ich `href` yo'qligi

- **Fayl:** `index.html` (18 va 24-qatorlar)
- **Muammo:**
  ```html
  <link rel="icon" data-app-icon>
  <link rel="apple-touch-icon" data-app-icon>
  ```
  `data-app-icon` atributi bor, lekin dastlabki `href` ko'rsatilmagan. JS skriptlar yuklanib ishga tushguncha brauzer avtomatik ravishda `/favicon.ico` ga so'rov yuborib konsolda ortiqcha 404 xatosini hosil qiladi.
- **Tuzatish:**
  Boshlang'ich qiymat sifatida `href="assets/icons/app-icon.png"` berib qo'yish.

---

## 7. ⚙️ DEPLOY VA INFRATUZILMA KAMCHILIKLARI

### [U-03] `deploy.sh` da `--all-changed` rejimi faqat JS/CSS fayllarni ko'rishi

- **Fayl:** `deploy.sh` (40–42-qatorlar)
- **Muammo:**
  ```bash
  mapfile -t FILES < <(git status --porcelain . | awk '{print $NF}' \
    | grep -E '\.(js|css)$' | sed 's|^yordamchi/yordamchi-sayt/||')
  ```
  Agar dasturchi `manifest.webmanifest`, `assets/md_books/`, yoki `database/schema.sql` fayllarini o'zgartirib, `./deploy.sh --all-changed` qilsa, ushbu fayllar yuklanmasdan serverda eski holicha qolib ketadi.
- **Tuzatish:**
  Ruxsat etilgan kengaytmalar ro'yxatiga `md`, `webmanifest`, `json`, `svg`, `png`, `sql` larni ham qo'shish.

---

## 8. 🚀 AMALGA OSHIRISH VA TUZATISH REJASI

Ushbu kamchiliklarni bartaraf etish uchun quyidagi ketma-ketlikda amallarni bajarish tavsiya etiladi:

### 1-Bosqich (Kritik tuzatishlar — darhol):
1. `index.html` (82-qator): `app-icon-192.png` o'rniga `custom-app-icon-192.png` qo'yish.
2. `assets/js/app2/auth.js` (370-qator): `checkLoop` ga `if (!document.body.contains(el)) return;` shartini kiritish.
3. `assets/js/core/tts.js` (256-qator): `interrupted` va `canceled` holatlarida kutayotgan callback'ni `fire(null)` bilan bo'shatish.

### 2-Bosqich (Xavfsizlik va Ma'lumotlar):
4. `backend_py/app/handlers/auth.py` (130-qator): "admin" hisobida `role="admin"` va `ruxsatlar=["*"]` to'g'ri o'rnatilishini ta'minlash.
5. `assets/js/app2/settings.js`: `localStorage.setItem` larni `try/catch` bilan o'rash va rasmlar hajmini nazorat qilish.
6. `assets/js/app2/home.js`: Stories'dagi "210 ta fe'l" matnini "229 ta fe'l" ga o'zgartirish.

### 3-Bosqich (Tozalash va Optimallashtirish):
7. `assets/video/losnhaazpv.mp4` (5.1 MB) ortiqcha faylini o'chirish.
8. `assets/js/app2/auth.js` (99-qator): Video manzilidagi boshlang'ich `/` ni olib tashlash.
9. `assets/js/app2/core.js`: `safeUrl` funksiyasida nisbiy rasm yo'llariga ruxsat berish.
10. `assets/css/app.css`: Yon panel uchun `100dvh` qo'llash.
11. `service-worker.js`: MD kitoblar yo'llarini precache ro'yxatiga qo'shish.
12. `deploy.sh`: Kengaytmalarni kengaytirish.

---
*Hisobot tizimning barcha qismlarini to'liq tekshirish va sinovdan o'tkazish orqali shakllantirildi.*
