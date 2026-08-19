/* Yordamchi service worker — OFFLINE REJIM.
 *
 * Uch qatlam:
 *  1) App shell (HTML/CSS/JS) — o'rnatishda oldindan keshlanadi, shuning uchun
 *     ilova internetsiz ham ochiladi (avval hech bo'lmasa bir marta kirilgan bo'lsa).
 *  2) Statik fayllar — stale-while-revalidate: darhol keshdan beriladi, orqa
 *     fonda yangilanadi.
 *  3) API O'QISH so'rovlari — network-first: internet bo'lsa yangisi, bo'lmasa
 *     oxirgi muvaffaqiyatli javob keshdan beriladi. Odatda faqat GET, ammo
 *     Boostday o'qishlari POST bilan ketadi, shuning uchun tanasi natijaga
 *     ta'sir qilmaydigan bir nechta POST o'qishga ham ruxsat berilgan
 *     (`CACHEABLE_POST`). YOZISH so'rovlari HECH QACHON keshlanmaydi —
 *     offline'da ular xato beradi va ilova o'z navbatiga qo'yadi.
 */
const VERSION = '20260812new6';
const SHELL_CACHE = 'yordamchi-shell-' + VERSION;
const DATA_CACHE = 'yordamchi-data-' + VERSION;

/* App shell ro'yxati QO'LDA yozilmaydi — index.html ning o'zidan o'qiladi.
   Sabab: har deployda asset versiyalari (`?v=`) o'zgaradi; qo'lda yozilgan
   ro'yxat darrov eskiradi va brauzer boshqa URL so'rab, kesh ishlamay
   qoladi (tekshiruvda aynan shunday nomuvofiqlik topilgan edi).
   Shu yondashuvda ro'yxat hech qachon eskirmaydi. */
async function shellUrls() {
  const urls = new Set(['./', './index.html']);
  try {
    const res = await fetch('./index.html', { cache: 'no-store' });
    const html = await res.text();
    const re = /(?:src|href)="((?:\.\/)?(?:assets\/|manifest\.webmanifest)[^"]*)"/g;
    let m;
    while ((m = re.exec(html)) !== null) {
      urls.add(m[1].startsWith('./') ? m[1] : './' + m[1]);
    }
  } catch (e) {
    // index.html o'qilmasa — hech bo'lmasa shell qoladi
  }
  return [...urls];
}

/* Offline'da ham ko'rsatish mumkin bo'lgan O'QISH amallari.
   Ro'yxat QO'LDA yozilmaydi — sayt bilan BITTA fayldan o'qiladi, aks holda
   ikki nusxa uzilib qolardi (App shell ro'yxatida ham shu yondashuv). */
importScripts('./assets/js/core/read-actions.js?v=' + VERSION);
const READ_ACTIONS = new Set(self.READ_ACTIONS || []);
const CACHEABLE_POST = new Set(self.CACHEABLE_POST_ACTIONS || []);

/* Bitta fayl yiqilsa butun jarayon to'xtamasin — har birini alohida qo'shamiz.
   Hammasini bir vaqtda so'rash ba'zan tasodifiy yiqilishga olib keladi
   (sinovda 24 tadan bittasi shunday tushib qolgan), shuning uchun:
   kichik guruhlarda yuboramiz va yiqilganlarni bir marta QAYTA urinamiz. */
async function addAll(cache, urls) {
  const failed = [];
  const BATCH = 6;
  for (let i = 0; i < urls.length; i += BATCH) {
    const part = urls.slice(i, i + BATCH);
    await Promise.all(part.map((u) =>
      cache.add(u).catch(() => { failed.push(u); })
    ));
  }
  return failed;
}

async function precache() {
  const list = await shellUrls();
  const c = await caches.open(SHELL_CACHE);
  const failed = await addAll(c, list);
  if (failed.length) await addAll(c, failed);   // ikkinchi urinish
}

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(precache());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => (k === SHELL_CACHE || k === DATA_CACHE ? null : caches.delete(k))));

    /* O'ZINI TIKLASH: brauzer joy bo'shatish uchun keshni tozalashi mumkin,
       yoki SW fayli o'zgarmagani uchun `install` qayta ishlamasligi mumkin
       (sinovda aynan shu holat kuzatildi: kesh qo'lda o'chirilgach, bir xil
       SW qayta ro'yxatdan o'tkazilsa precache umuman ishlamadi). Shuning
       uchun har faollashuvda kesh yetarlimi tekshiramiz. */
    const c = await caches.open(SHELL_CACHE);
    const have = await c.keys();
    if (have.length < 5) await precache();

    await self.clients.claim();
  })());
});

/* Sahifa "keshni tekshir" desa ham tiklaymiz (qo'shimcha himoya). */
self.addEventListener('message', (e) => {
  if (e.data === 'precache') e.waitUntil(precache());
});

/* ============================================================
   TELEFON BILDIRISHNOMASI (Web Push)
   Server VAPID kaliti bilan imzolangan xabar yuboradi; ilova YOPIQ
   bo'lsa ham brauzer service worker'ni uyg'otadi va bildirishnoma
   qulflangan ekranda chiqadi (Instagram/YouTube kabi).
   ============================================================ */
self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = { title: (e.data && e.data.text()) || '' }; }
  const title = d.title || 'Yordamchi';
  e.waitUntil(self.registration.showNotification(title, {
    body: d.body || '',
    icon: './assets/icons/custom-app-icon-192.png',
    badge: './assets/icons/custom-app-icon-192.png',
    /* `tag` — bir xil eslatma ustma-ust to'planib ketmasin: yangisi
       eskisining o'rnini oladi. */
    tag: d.tag || 'yordamchi',
    renotify: true,
    vibrate: [140, 70, 140],
    data: { url: d.url || '/' }
  }));
});

/* Bildirishnoma bosilganda: ilova allaqachon ochiq bo'lsa o'sha oynani
   oldinga chiqaramiz (yangi oyna ochmaymiz), aks holda ochamiz. */
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const target = (e.notification.data && e.notification.data.url) || '/';
  e.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if (c.url.indexOf(self.location.origin) === 0) {
        await c.focus();
        if ('navigate' in c && target !== '/') { try { await c.navigate(target); } catch (err) {} }
        return;
      }
    }
    await self.clients.openWindow(target);
  })());
});

/* API kesh kaliti: `t=` (cache-buster) va boshqa tasodifiy parametrlarni
   olib tashlaymiz — aks holda har so'rov yangi kalit yasab, kesh hech qachon
   topilmaydi (storage_bootstrap aynan shunday `&t=` bilan chaqiriladi). */
function dataCacheKey(url) {
  const u = new URL(url);
  u.searchParams.delete('t');
  u.searchParams.delete('_');
  u.searchParams.delete('cb');
  return u.toString();
}

function isApi(url) {
  return url.pathname === '/api' || url.pathname.startsWith('/api/');
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Boostday bot'ning TO'G'RIDAN-TO'G'RI yo'li (dinamik) — keshlanmaydi.
  // (`/api?action=boost_*` bu emas — u quyida, o'qish bo'lsa keshlanadi.)
  if (url.pathname.startsWith('/boost')) return;

  const action = isApi(url) ? (url.searchParams.get('action') || '') : '';

  /* Odatda faqat GET keshlanadi. Ammo Boostday o'qishlari POST bilan
     yuboriladi (boost.js har safar `{}` payload beradi), shuning uchun
     tanasi natijaga ta'sir qilmaydigan o'qishlarga ruxsat beramiz —
     ular bo'lmasa bosh sahifadagi kunlik statistika offline'da bo'sh
     qolardi. Kesh kaliti URL, shuning uchun ro'yxat qat'iy cheklangan
     (`CACHEABLE_POST`, read-actions.js ga qarang). */
  if (req.method !== 'GET' && !(req.method === 'POST' && CACHEABLE_POST.has(action))) return;

  // --- API ---
  if (isApi(url)) {
    if (!READ_ACTIONS.has(action)) return;       // yozuv yoki noma'lum — tegmaymiz
    const key = dataCacheKey(req.url);
    e.respondWith(
      fetch(req)
        .then((r) => {
          if (r && r.status === 200) {
            const copy = r.clone();
            caches.open(DATA_CACHE).then((c) => c.put(key, copy));
          }
          return r;
        })
        .catch(() =>
          caches.open(DATA_CACHE)
            .then((c) => c.match(key))
            .then((cached) => cached || new Response(
              JSON.stringify({ success: false, error: 'Oflayn: bu ma\'lumot hali keshlanmagan.', offline: true }),
              { status: 503, headers: { 'Content-Type': 'application/json' } }
            ))
        )
    );
    return;
  }

  // --- Navigatsiya (HTML) — network-first, offline'da shell ---
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then((r) => {
          const copy = r.clone();
          caches.open(SHELL_CACHE).then((c) => c.put('./index.html', copy));
          return r;
        })
        .catch(() => caches.match('./index.html', { ignoreSearch: true }))
    );
    return;
  }

  // --- Statik (css/js/img/font) — stale-while-revalidate ---
  e.respondWith(
    caches.match(req).then((cached) => {
      const net = fetch(req)
        .then((r) => {
          if (r && r.status === 200) {
            const copy = r.clone();
            caches.open(SHELL_CACHE).then((c) => c.put(req, copy));
          }
          return r;
        })
        .catch(() => cached);
      return cached || net;
    })
  );
});
