/* ---------- .md fayllar uchun "O'qish uslubi" ----------
 *
 * Darsliklar `.md` fayldan chiziladi (`App.md()` -> `.md-content`).
 * Ilova ichidagi odatiy uslub ixcham: ro'yxatlar zich, sarlavhalar kichik,
 * matn kengligi cheklanmagan. Bu qisqa izohlar uchun to'g'ri, lekin uzun
 * darsni o'qish uchun charchatadi.
 *
 * Yoqilganda matn UZOQ O'QISH uchun sozlanadi: yiriklashtirilgan shrift,
 * kengaytirilgan qator oralig'i, cheklangan satr kengligi, sarlavhalar
 * orasida havo, kod bloklari alohida panel bo'lib ajraladi.
 *
 * NIMA UCHUN FAQAT CSS
 * ====================
 * Markdown chizuvchi (`App._mdToHtml`) TEGILMAYDI. U h1-h6, p, ul/ol,
 * pre/code, blockquote, table, hr chiqaradi — bularning hammasi uslub
 * bilan o'zgartiriladi. Chizuvchini o'zgartirish ikkita yo'l hosil
 * qilardi va ular vaqt o'tib bir-biridan uzoqlashardi.
 *
 * Uslub `<html>` elementiga `md-claude` klassi sifatida qo'yiladi, ya'ni
 * sahifa qayta chizilganda ham saqlanadi va HAR JOYDA (darslik, qoidalar,
 * arxiv, kutubxona) bir vaqtda ishlaydi.
 */
(function (root) {
  'use strict';

  var KEY = 'md_read_theme_v1';
  var CLS = 'md-claude';

  function isOn() {
    try { return localStorage.getItem(KEY) === '1'; } catch (e) { return false; }
  }

  function apply() {
    var el = root.document && root.document.documentElement;
    if (!el) return;
    if (isOn()) el.classList.add(CLS); else el.classList.remove(CLS);
  }

  function set(on) {
    try { localStorage.setItem(KEY, on ? '1' : '0'); } catch (e) {}
    apply();
  }

  root.MdTheme = { isOn: isOn, set: set, apply: apply, toggle: function () { set(!isOn()); return isOn(); } };

  /* Sahifa ochilishida darhol qo'llanadi. `storage_bootstrap` tugagach
     qayta qo'llanadi — boshqa qurilmada yoqilgani shu yerda ham
     ko'rinishi uchun (kalit serverga sinxronlanadi). */
  apply();
  try {
    root.addEventListener('remote-storage:refreshed', apply);
    root.document.addEventListener('DOMContentLoaded', apply);
  } catch (e) {}
})(window);
