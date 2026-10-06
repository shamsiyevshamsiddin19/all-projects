/* =================================================================
   Google orqali kirish (Firebase)

   NEGA POPUP EMAS, YO'NALTIRISH?
     Avval signInWithPopup ishlatilgandi. U shunday ishlaydi:
       1. Kichik oyna ochiladi
       2. Google da akkaunt tanlanadi
       3. Oyna ASOSIY SAHIFAGA xabar yuboradi (postMessage)
       4. Oyna yopiladi

     3-qadam ko'p brauzerlarda buziladi: Chrome uchinchi tomon
     saqlash va oynalararo aloqani cheklaydi. Natijada oyna oq
     bo'lib yopiladi, asosiy sahifa esa hech narsa olmaydi.

     signInWithRedirect da oyna umuman yo'q: butun sahifa Google ga
     o'tadi, keyin o'zimizga qaytadi. Oynalararo aloqa kerak emas,
     shuning uchun ancha ishonchli.

   MUHIM: token brauzerda tekshirilmaydi. Haqiqiy tekshiruv
   serverda — views.py dagi google_login.
   ================================================================= */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithRedirect,
  getRedirectResult,
  signOut,
} from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';

const tugma = document.querySelector('[data-google-login]');

if (tugma) {
  const xatoJoyi = document.querySelector('[data-google-error]');
  const config = JSON.parse(
    document.getElementById('firebase-config').textContent
  );

  const app = initializeApp(config);
  const auth = getAuth(app);
  auth.useDeviceLanguage();

  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: 'select_account' });

  function xatoKorsat(matn) {
    if (xatoJoyi) {
      xatoJoyi.textContent = matn;
      xatoJoyi.hidden = false;
    }
    tugma.disabled = false;
    tugma.classList.remove('is-loading');
  }

  function kutish(yoq) {
    tugma.disabled = yoq;
    tugma.classList.toggle('is-loading', yoq);
  }

  /* Firebase xato kodini o'zbekcha izohga aylantiradi */
  function izoh(e) {
    const kod = e && e.code ? e.code : '';
    if (kod === 'auth/unauthorized-domain') {
      return 'Bu manzil Firebase da ruxsat etilmagan. Konsolda ' +
             'Authentication -> Settings -> Authorized domains ga qo\'shing.';
    }
    if (kod === 'auth/operation-not-allowed') {
      return 'Firebase konsolida Google usuli yoqilmagan.';
    }
    if (kod === 'auth/network-request-failed') {
      return 'Internet bilan aloqa yo\'q.';
    }
    if (kod === 'auth/web-storage-unsupported') {
      return 'Brauzer saqlashga ruxsat bermayapti. Cookie larni yoqing ' +
             'yoki yashirin rejimdan chiqing.';
    }
    // Noma'lum xatoda kodning o'zini ko'rsatamiz — shunda uni
    // izlash yoki aytib berish mumkin bo'ladi.
    return 'Google bilan kirib bo\'lmadi: ' + (kod || e.message || 'noma\'lum xato');
  }

  /* Tokenni serverga yuboradi. Server uni tekshirib sessiya ochadi. */
  async function tokenniYubor(token) {
    const forma = new FormData();
    forma.append('id_token', token);
    forma.append('csrfmiddlewaretoken', tugma.dataset.csrf);

    const javob = await fetch(tugma.dataset.googleLoginUrl, {
      method: 'POST',
      body: forma,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    const natija = await javob.json();

    if (natija.ok) {
      // Firebase sessiyasi endi kerak emas — Django sessiyasi ochildi
      signOut(auth).catch(() => {});
      window.location = natija.keyingi || '/';
    } else {
      xatoKorsat(natija.xato || 'Server tokenni qabul qilmadi.');
    }
  }

  /* --------------------------------------------------------------
     1-QISM: Google dan qaytganimizda
     Sahifa har yuklanganda tekshiramiz — yo'naltirishdan keyin
     natija shu yerda kutib turadi.
     -------------------------------------------------------------- */
  (async function qaytganNatija() {
    kutish(true);
    try {
      const natija = await getRedirectResult(auth);
      if (natija && natija.user) {
        const token = await natija.user.getIdToken();
        await tokenniYubor(token);
        return;               // sahifa almashadi, tugmani tiklamaymiz
      }
    } catch (e) {
      xatoKorsat(izoh(e));
      return;
    }
    kutish(false);            // natija yo'q — oddiy holat, tugma tayyor
  })();

  /* --------------------------------------------------------------
     2-QISM: Tugma bosilganda
     Butun sahifa Google ga o'tadi. Qaytganda 1-qism ushlab oladi.
     -------------------------------------------------------------- */
  tugma.addEventListener('click', async () => {
    if (xatoJoyi) xatoJoyi.hidden = true;
    kutish(true);
    try {
      await signInWithRedirect(auth, provider);
      // Bu yerga yetib kelmaydi — brauzer allaqachon Google ga ketgan
    } catch (e) {
      xatoKorsat(izoh(e));
    }
  });
}
