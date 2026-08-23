/* O'QISH amallari ro'yxati — YAGONA MANBA.
 *
 * Bu fayl IKKI joyda yuklanadi:
 *   1) index.html   -> `window.READ_ACTIONS` (App.call ishlatadi)
 *   2) service-worker.js -> `importScripts()` orqali `self.READ_ACTIONS`
 * `self` ikkala muhitda ham mavjud, shuning uchun bitta fayl yetarli.
 *
 * NEGA YAGONA MANBA: ilgari ro'yxat faqat service-worker.js ichida edi va
 * u yerda yangi amal qo'shishni unutish oson bo'lardi. Endi ro'yxat bir
 * joyda — uzilib qolishi mumkin emas.
 *
 * IKKI TOIFA:
 *   READ_ACTIONS      — o'qish amallari. Offline'da bularni "keyin
 *                       yuboriladi" navbatiga QO'YMASLIK kerak: o'qishni
 *                       qayta yuborishning ma'nosi yo'q va chaqiruvchi
 *                       ma'lumot o'rniga soxta "muvaffaqiyat" olardi.
 *   CACHEABLE_POST    — POST bilan yuboriladigan, lekin aslida O'QISH
 *                       bo'lgan amallar. Kesh kaliti URL bo'lgani uchun
 *                       bu yerga FAQAT tanasi (body) natijaga ta'sir
 *                       qilmaydigan amallar kiradi — aks holda turli
 *                       so'rovlar bitta kalitga urilib, noto'g'ri javob
 *                       qaytarilardi (masalan `boost_get?id=` — kirmaydi).
 */
(function (root) {
  var READ = [
    'storage_bootstrap',
    'get_activity_log',
    'get_data',
    'get_dict_data',
    'get_mistakes',
    'list_mistake_snapshots',
    'get_mistake_snapshot',
    'get_quiz_results',
    'list_wrong_snapshots',
    'get_wrong_snapshot',
    'get_structure',
    'get_topic',
    'get_topics',
    'sport_get_all',
    'lms_schedule',
    'lms_status',
    /* Boostday (botga proxy qilinadi). Bular ham o'qish — bosh sahifadagi
       "Kunlik statistika" va Boostday bo'limi shularga tayanadi. */
    'boost_list',
    'boost_get',
    'boost_stats',
    'boost_channels',
    'boost_habits_list'
  ];

  var CACHEABLE_POST = [
    'boost_list',
    'boost_stats',
    'boost_channels',
    'boost_habits_list'
    /* `boost_get` ATAYLAB yo'q: uning `id` si tanada keladi, URL esa
       hammasi uchun bir xil — keshlansa boshqa rejaning ma'lumoti
       qaytib qolardi. */
  ];

  root.READ_ACTIONS = READ;
  root.CACHEABLE_POST_ACTIONS = CACHEABLE_POST;
})(typeof self !== 'undefined' ? self : this);
