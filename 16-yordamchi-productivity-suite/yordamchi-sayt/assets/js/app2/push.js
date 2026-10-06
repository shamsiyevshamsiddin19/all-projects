/* Telefon bildirishnomasi (Web Push) — brauzer tomoni.
 *
 * Telegram xabaridan farqi: bildirishnoma qulflangan ekranda, tizim
 * panelida chiqadi va ilova ochiq bo'lishi shart emas — xuddi
 * Instagram/YouTube kabi.
 *
 * Tartib:
 *   1. Foydalanuvchi tugmani bosadi -> brauzer RUXSAT so'raydi.
 *      (Ruxsat faqat foydalanuvchi harakatidan keyin so'ralishi kerak,
 *      aks holda brauzer so'rovni jimgina rad etadi.)
 *   2. `PushManager.subscribe()` server ochiq kaliti bilan obuna bo'ladi.
 *   3. Obuna serverga saqlanadi (`push_subscribe`).
 *   4. Eslatma vaqti kelganda bot o'sha obunaga xabar yuboradi.
 */
(function () {
  'use strict';

  function call(action, payload) {
    return App.call('boost_' + action, payload || {});
  }

  /* base64url -> Uint8Array (VAPID kaliti shu ko'rinishda keladi) */
  function urlB64ToUint8(base64) {
    var pad = '='.repeat((4 - base64.length % 4) % 4);
    var b64 = (base64 + pad).replace(/-/g, '+').replace(/_/g, '/');
    var raw = atob(b64);
    var out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }

  function supported() {
    return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  }

  /* Qurilma nima deydi: yoqilganmi, rad etilganmi, qo'llab-quvvatlanmaydimi */
  function state() {
    if (!supported()) return 'unsupported';
    if (Notification.permission === 'denied') return 'denied';
    if (Notification.permission === 'granted') return 'granted';
    return 'default';
  }

  function currentSub() {
    if (!supported()) return Promise.resolve(null);
    return navigator.serviceWorker.ready
      .then(function (reg) { return reg.pushManager.getSubscription(); })
      .catch(function () { return null; });
  }

  function subToPayload(sub) {
    var j = sub.toJSON();
    return {
      endpoint: j.endpoint,
      p256dh: (j.keys || {}).p256dh || '',
      auth: (j.keys || {}).auth || '',
      ua: (navigator.userAgent || '').slice(0, 200)
    };
  }

  /* Yoqish — ruxsat so'raydi, obuna bo'ladi va serverga saqlaydi */
  function enable() {
    if (!supported()) {
      return Promise.reject(new Error('Bu brauzer bildirishnomani qo\'llamaydi'));
    }
    if (Notification.permission === 'denied') {
      return Promise.reject(new Error(
        'Bildirishnoma brauzer sozlamalarida bloklangan — avval o\'sha yerdan ruxsat bering'));
    }

    return Notification.requestPermission().then(function (perm) {
      if (perm !== 'granted') throw new Error('Ruxsat berilmadi');
      return call('push_key');
    }).then(function (j) {
      if (!j.key) throw new Error('Server kaliti sozlanmagan');
      return navigator.serviceWorker.ready.then(function (reg) {
        return reg.pushManager.getSubscription().then(function (old) {
          if (old) return old;
          return reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlB64ToUint8(j.key)
          });
        });
      });
    }).then(function (sub) {
      return call('push_subscribe', subToPayload(sub));
    });
  }

  function disable() {
    return currentSub().then(function (sub) {
      if (!sub) return { ok: true };
      var ep = sub.toJSON().endpoint;
      return sub.unsubscribe().catch(function () { return true; })
        .then(function () { return call('push_unsubscribe', { endpoint: ep }); });
    });
  }

  function test() { return call('push_test'); }

  App.actions.pushEnable = function () {
    App.toast('Ruxsat so\'ralmoqda...');
    enable().then(function (j) {
      App.toast('✅ Bildirishnoma yoqildi');
      if (window.PushUI && PushUI.repaint) PushUI.repaint();
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };
  App.actions.pushDisable = function () {
    disable().then(function () {
      App.toast('Bildirishnoma o\'chirildi');
      if (window.PushUI && PushUI.repaint) PushUI.repaint();
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };
  App.actions.pushTest = function () {
    App.toast('Yuborilmoqda...');
    test().then(function (j) { App.toast('✅ ' + (j.message || 'Yuborildi')); })
      .catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  window.Push = {
    supported: supported, state: state, enable: enable,
    disable: disable, test: test, currentSub: currentSub
  };
})();
