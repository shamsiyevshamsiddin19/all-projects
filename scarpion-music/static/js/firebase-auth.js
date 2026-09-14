/* =================================================================
   Google orqali kirish (Firebase)

   Bu fayl <script type="module"> sifatida yuklanadi — shuning uchun
   ichida import ishlatsa bo'ladi. Firebase SDK Google'ning CDN sidan
   keladi, loyihaga yuklab olinmaydi.

   Oqim:
     1. "Google bilan kirish" bosiladi
     2. Google oynasi ochiladi (signInWithPopup)
     3. Google ID token beradi
     4. Tokenni serverga yuboramiz (/google-kirish/)
     5. Server uni TEKSHIRADI va sessiya ochadi
     6. Bosh sahifaga o'tamiz

   MUHIM: token brauzerda tekshirilmaydi. Brauzerdagi har qanday
   tekshiruvni chetlab o'tish mumkin — haqiqiy tekshiruv serverda
   (views.py dagi google_login).
   ================================================================= */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
} from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';

const tugma = document.querySelector('[data-google-login]');
if (tugma) {
  // Sozlamalar shablondan keladi (context_processors.py -> firebase_config)
  const config = JSON.parse(
    document.getElementById('firebase-config').textContent
  );

  const app = initializeApp(config);
  const auth = getAuth(app);
  auth.useDeviceLanguage();          // Google oynasi brauzer tilida chiqadi

  const provider = new GoogleAuthProvider();
  // Har safar akkaunt tanlash oynasi chiqsin — bitta brauzerda
  // bir nechta Google akkaunti bo'lishi mumkin.
  provider.setCustomParameters({ prompt: 'select_account' });

  const xatoJoyi = document.querySelector('[data-google-error]');

  function xatoKorsat(matn) {
    if (xatoJoyi) {
      xatoJoyi.textContent = matn;
      xatoJoyi.hidden = false;
    }
    tugma.disabled = false;
    tugma.classList.remove('is-loading');
  }

  tugma.addEventListener('click', async () => {
    if (xatoJoyi) xatoJoyi.hidden = true;
    tugma.disabled = true;
    tugma.classList.add('is-loading');

    let token;
    try {
      const natija = await signInWithPopup(auth, provider);
      token = await natija.user.getIdToken();
    } catch (e) {
      // Foydalanuvchi oynani yopdi — bu xato emas, jim qolamiz
      if (e.code === 'auth/popup-closed-by-user' ||
          e.code === 'auth/cancelled-popup-request') {
        tugma.disabled = false;
        tugma.classList.remove('is-loading');
        return;
      }
      if (e.code === 'auth/unauthorized-domain') {
        xatoKorsat('Bu manzil Firebase da ruxsat etilmagan. ' +
                   'Konsolda Authorized domains ga qo\'shing.');
        return;
      }
      if (e.code === 'auth/operation-not-allowed') {
        xatoKorsat('Firebase konsolida Google usuli yoqilmagan.');
        return;
      }
      xatoKorsat('Google bilan kirib bo\'lmadi: ' + (e.code || e.message));
      return;
    }

    // Tokenni serverga yuboramiz
    try {
      const forma = new FormData();
      forma.append('id_token', token);
      forma.append('csrfmiddlewaretoken', tugma.dataset.csrf);

      // data-google-login-url  ->  dataset.googleLoginUrl
      const javob = await fetch(tugma.dataset.googleLoginUrl, {
        method: 'POST',
        body: forma,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const natija = await javob.json();

      if (natija.ok) {
        // Firebase sessiyasi endi kerak emas — bizning Django
        // sessiyamiz ochildi. Brauzerda ortiqcha holat qoldirmaymiz.
        signOut(auth).catch(() => {});
        window.location = natija.keyingi || '/';
      } else {
        xatoKorsat(natija.xato || 'Server tokenni qabul qilmadi.');
      }
    } catch (e) {
      xatoKorsat('Serverga ulanib bo\'lmadi.');
    }
  });
}
