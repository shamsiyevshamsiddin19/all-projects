/* Subtitr Mini App — frontend (bo'limlar: Yangi / Tarix / Profil). */
(function () {
  "use strict";

  var tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  if (tg) { try { tg.ready(); tg.expand(); } catch (e) {} }
  var INIT = tg ? (tg.initData || "") : "";
  var inTG = !!(tg && tg.platform && tg.platform !== "unknown");
  var TGUSER = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : null;

  // Brauzer token (Telegram tashqarisida — bot bergan /app?t=TOKEN havolasi).
  // URL'dan o'qiladi va localStorage'da saqlanadi (keyingi tashriflar uchun).
  var WEB_TOKEN = "";
  try {
    var _m = location.search.match(/[?&]t=([^&]+)/);
    if (_m) {
      WEB_TOKEN = decodeURIComponent(_m[1]);
      localStorage.setItem("subtitr_web_token", WEB_TOKEN);
      // URL'dan tokenni tozalaymiz (tarix/ulashishда ko'rinmasin)
      try { history.replaceState(null, "", location.pathname); } catch (e) {}
    } else if (!inTG) {
      WEB_TOKEN = localStorage.getItem("subtitr_web_token") || "";
    }
  } catch (e) {}

  function haptic(t) {
    try {
      if (tg && tg.HapticFeedback) {
        if (t === "sel") tg.HapticFeedback.selectionChanged();
        else tg.HapticFeedback.notificationOccurred(t);
      }
    } catch (e) {}
  }

  // ---- ikonkalar ----
  var ICON = {
    type: '<polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/>',
    globe: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    layers: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    ai: '<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/>',
    audio: '<line x1="4" y1="10" x2="4" y2="14"/><line x1="8" y1="6" x2="8" y2="18"/><line x1="12" y1="9" x2="12" y2="15"/><line x1="16" y1="5" x2="16" y2="19"/><line x1="20" y1="10" x2="20" y2="14"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    film: '<rect x="2" y="2" width="20" height="20" rx="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="17" x2="22" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    check: '<polyline points="20 6 9 17 4 12"/>',
    card: '<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
    text: '<line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="14" y2="18"/>',
    book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    grad: '<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1 2.7 2.5 6 2.5s6-1.5 6-2.5v-5"/>'
  };
  function svg(name) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + (ICON[name] || "") + "</svg>";
  }

  // Bot bilan bir xil tartib: subtitr rejimlari -> fayl/matn -> audio
  var ALL_MODES = ["original", "translate", "dual", "dual_vocab", "srt", "transcript", "vocabulary", "audio"];
  var MODE_ICON = { original: "type", translate: "globe", dual: "layers", dual_vocab: "grad", srt: "file", transcript: "text", vocabulary: "book", audio: "audio" };
  var MODE_LABELS = { original: "Original", translate: "Tarjima", dual: "Ikki qatlam", dual_vocab: "Ikki qatlam + lug'at", srt: ".srt fayl", transcript: "Matn", vocabulary: "Lug'at", audio: "Audio" };
  var MODE_DESC = { original: "Asl tilда", translate: "Boshqa tilga", dual: "Asl + tarjima", dual_vocab: "Subtitr + suzuvchi lug'at", srt: "Faqat fayl", transcript: "txt / pdf", vocabulary: "So'zlar + tarjima", audio: "Videodan ovoz (MP3)" };

  // Qulflangan rejim modali — har rejim uchun natijaga yo'naltirilgan matn
  var MODE_BENEFIT = {
    translate: "Videongizni butun dunyoga oching. O'zbek, rus yoki ingliz tiliga avtomatik tarjima — chet ellik tomoshabinlar ham sizni tushunadi.",
    dual: "Asl til va tarjima bitta ekranda. Til o'rganuvchilar va xalqaro auditoriya uchun eng kuchli format.",
    dual_vocab: "Ikki qatlam subtitr ustiga — ekranda aytilgan so'zlar tarjimasi bilan suzib chiqadi. Til o'rganish uchun eng kuchli format.",
    srt: "Subtitr faylini yuklab oling va istalgan joyda ishlating — YouTube, montaj dasturlari yoki o'zingiz tahrirlash uchun.",
    transcript: "Videodagi barcha gaplar matn ko'rinishida — chiroyli PDF yoki txt qilib yuklab oling. Maqola, konspekt yoki tahrirlash uchun qulay.",
    vocabulary: "Videodagi barcha so'zlar tarjimasi bilan — tayyor PDF lug'at (2 ustun, guruhlangan). Til o'rganuvchilar uchun ideal.",
    audio: "Videodan faqat ovozni ajratib oling — MP3 fayl. Podkast, musiqa yoki tinglash uchun qulay."
  };
  var UNLOCKS = [
    "Tarjima — o'zbek, rus va ingliz tillariga",
    "Ikki qatlam — asl til va tarjima birga",
    ".srt fayl — tahrirlash uchun eksport",
    "Subtitr uslubini to'liq sozlash",
    "Kuniga ko'proq va uzunroq videolar"
  ];
  var LANGS = { uz: "O'zbek", ru: "Rus", en: "Ingliz", auto: "Avto" };
  var SRC_ORDER = ["auto", "ru", "en", "uz"];
  var TGT_ORDER = ["uz", "ru", "en"];
  var TRANSLATE_MODES = ["translate", "dual", "dual_vocab", "vocabulary"];
  var LINK_RE = /https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be|instagram\.com)/i;
  var HIST_KEY = "subtitr_history";
  var STYLE_KEY = "subtitr_style";
  var STYLE_DEFAULTS = { text_color: "#FFFFFF", outline_color: "#000000",
    trans_color: "#FFE580", font_size: "medium", position: "bottom", bold: true, box: false };
  var SIZE_PX = { small: 16, medium: 21, large: 27 };

  var el = function (id) { return document.getElementById(id); };
  function api(path, opts) {
    opts = opts || {};
    opts.headers = opts.headers || {};
    opts.headers["X-Init-Data"] = INIT;
    if (WEB_TOKEN) opts.headers["X-Web-Token"] = WEB_TOKEN;
    return fetch(path, opts);
  }
  function escapeHtml(s) { var d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }

  var state = { method: "file", file: null, modes: ["original"], lang: null, busy: false,
                poll: null, view: "idle", section: "create", botUser: "", style: null,
                allowed: ["original"], prices: null, payEnabled: false,
                stageId: null, staging: false, staged: false, stageXhr: null,
                pendingSubmit: false, jobId: null, donAmount: null };

  // ----------------------------------------------------------- profil
  function loadProfile() {
    api("/api/me", { method: "POST" })
      .then(function (r) { if (r.status === 401) throw new Error("auth"); return r.json(); })
      .then(function (p) {
        el("planChip").textContent = p.plan_title || p.plan;
        el("pPlan").textContent = p.plan_title || p.plan;
        el("pUsed").textContent = p.daily === -1 ? p.used + " / ∞" : p.used + " / " + p.daily;
        el("pMax").textContent = p.max_minutes + " daq";
        el("dropHint").textContent = "MP4, MOV, MKV… (≤ " + p.max_mb + "MB)";
        state.prices = { basic: p.price_basic, premium: p.price_premium, days: p.sub_days || 30 };
        state.payEnabled = !!p.pay_enabled;
        setHeaderUser(p);
        buildModes(p.modes || ["original"]);
        renderProfile(p);
      })
      .catch(function (err) {
        el("planChip").textContent = "—";
        // Telegram tashqarisida va token yo'q — botga yo'naltiramiz
        if (!inTG && !WEB_TOKEN) { showAuthGate(); return; }
        el("formErr").textContent =
          (err && err.message === "auth")
            ? "Kirish muddati tugagan. Botda /web buyrug'i bilan yangi havola oling."
            : "Profil yuklanmadi. Internetni tekshiring yoki keyinroq urinib ko'ring.";
      });
  }

  // ----------------------------------------------------------- homiylar devori
  function fmtSum(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " so'm";
  }
  function loadDonors() {
    fetch("/api/donors")
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var list = el("donorsList");
        var empty = el("donorsEmpty");
        if (!list || !empty) return;
        var donors = (j && j.donors) || [];
        empty.classList.toggle("hidden", donors.length > 0);
        var html = "";
        for (var i = 0; i < donors.length; i++) {
          var d = donors[i];
          var initial = (d.name || "H").replace("@", "").charAt(0).toUpperCase();
          html += '<div class="donor-row">'
            + '<span class="donor-av">' + escapeHtml(initial) + "</span>"
            + '<div class="donor-main"><div class="donor-line">'
            + '<span class="donor-name">' + escapeHtml(d.name) + "</span>"
            + '<span class="donor-amt">' + escapeHtml(fmtSum(d.amount)) + "</span></div>"
            + (d.comment ? '<div class="donor-comment">' + escapeHtml(d.comment) + "</div>" : "")
            + "</div>"
            + '<span class="donor-date">' + escapeHtml(d.date || "") + "</span>"
            + "</div>";
        }
        list.innerHTML = html;
      })
      .catch(function () { /* devor yuklanmasa jim — profil ishlayveradi */ });
  }

  // ----------------------------------------------------------- auth gate (brauzer)
  function showAuthGate() {
    var gate = el("authGate");
    if (!gate) return;
    gate.classList.remove("hidden");
    // Bot username'ni ommaviy endpoint'dan olamiz
    fetch("/api/public").then(function (r) { return r.json(); }).then(function (p) {
      var bu = p.bot_username || "";
      var link = bu ? "https://t.me/" + bu : "#";
      var btn = el("gateBtn");
      btn.href = link;
      btn.onclick = function (e) {
        if (!bu) { e.preventDefault(); return; }
      };
    }).catch(function () {});
  }

  function openInBrowser() {
    api("/api/weblink", { method: "POST" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.url) {
          if (inTG) tg.openLink(j.url); else window.open(j.url, "_blank");
        }
      }).catch(function () {});
  }

  function setHeaderUser(p) {
    var first = TGUSER && TGUSER.first_name ? TGUSER.first_name : "";
    var name = first || (p.username ? "@" + p.username : "Profil");
    el("huName").textContent = name;
    var av = el("huAv");
    var photo = TGUSER && TGUSER.photo_url;
    if (photo) {
      av.style.backgroundImage = "url('" + photo + "')";
      av.classList.add("img");
      av.textContent = "";
    } else {
      av.style.backgroundImage = "";
      av.classList.remove("img");
      av.textContent = (first ? first[0] : (p.username ? p.username[0] : "U")).toUpperCase();
    }
  }

  function paintAvatar(avEl, fallbackChar) {
    var photo = TGUSER && TGUSER.photo_url;
    if (photo) {
      avEl.style.backgroundImage = "url('" + photo + "')";
      avEl.classList.add("img");
      avEl.textContent = "";
    } else {
      avEl.style.backgroundImage = "";
      avEl.classList.remove("img");
      avEl.textContent = (fallbackChar || "U").toUpperCase();
    }
  }

  function renderProfile(p) {
    state.botUser = p.bot_username || "";
    var first = TGUSER && TGUSER.first_name ? TGUSER.first_name : "";
    var name = first || (p.username ? "@" + p.username : "Foydalanuvchi");
    el("profName").textContent = name;
    paintAvatar(el("profAv"), first ? first[0] : (p.username ? p.username[0] : "U"));
    el("profPlan").textContent = p.plan_title || p.plan;
    el("profUntil").textContent = p.plan_until ? p.plan_until + " gacha" : "";
    el("profUsed").textContent = p.daily === -1 ? p.used + " / ∞" : p.used + " / " + p.daily;
    el("profMax").textContent = p.max_minutes;
    el("profModes").textContent = (p.modes || []).length;
    el("subBtn").classList.toggle("hidden", p.plan !== "free");
    el("styleBanner").classList.toggle("hidden", p.plan !== "free");
  }

  // ----------------------------------------------------------- rejim/til
  function buildModes(allowed) {
    state.allowed = allowed && allowed.length ? allowed : ["original"];
    if (!state.modes) state.modes = [];
    // Ruxsat etilmagan tanlovlarni olib tashlaymiz (tarif o'zgarsa)
    state.modes = state.modes.filter(function (m) { return state.allowed.indexOf(m) >= 0; });
    var c = el("modeSeg"); c.innerHTML = "";
    ALL_MODES.forEach(function (m) {
      var locked = state.allowed.indexOf(m) < 0;
      var on = state.modes.indexOf(m) >= 0;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "modechip" + (on ? " on" : "") + (locked ? " locked" : "");
      b.innerHTML =
        '<span class="mi">' + svg(MODE_ICON[m] || "type") + "</span>" +
        '<span class="mt"><span class="mn">' + (MODE_LABELS[m] || m) +
        '</span><span class="md">' + (MODE_DESC[m] || "") + "</span></span>" +
        (locked ? '<span class="lk">' + svg("lock") + "</span>"
                : (on ? '<span class="lk">' + svg("check") + "</span>" : ""));
      if (locked) {
        b.onclick = function () { openPaySheet(m); };
      } else {
        b.onclick = function () {
          haptic("sel");
          state.modes = [m];   // bitta rejim — exclusive tanlov
          buildModes(state.allowed); validate();
        };
      }
      c.appendChild(b);
    });
    buildLangs();
  }

  // ----------------------------------------------------------- obuna modali
  function fmtNum(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " "); }
  function perDay(price, days) {
    var d = Math.max(1, days || 30);
    return Math.round(price / d / 100) * 100;
  }

  function renderPlans() {
    var pr = state.prices || { basic: 30000, premium: 60000, days: 30 };
    var plans = [
      { key: "premium", name: "PREMIUM", price: pr.premium, reco: true, badge: "Eng foydali",
        feats: ["Cheksiz video", "Barcha rejimlar", "Tezroq navbat"], cta: "Premiumni olish" },
      { key: "basic", name: "BASIC", price: pr.basic, reco: false, badge: "",
        feats: ["Kuniga 10 video", "Barcha rejimlar", "30 daqiqagacha"], cta: "Basic olish" }
    ];
    var c = el("payPlans"); c.innerHTML = "";
    plans.forEach(function (p) {
      var pd = perDay(p.price, pr.days);
      var card = document.createElement("div");
      card.className = "plan-card" + (p.reco ? " reco" : "");
      card.innerHTML =
        (p.badge ? '<span class="plan-badge2">' + p.badge + "</span>" : "") +
        '<div class="plan-row"><span class="plan-name">' + p.name + "</span>" +
        '<span class="plan-price">' + fmtNum(p.price) + " <small>so'm/oy</small></span></div>" +
        '<div class="plan-perday">atigi ~' + fmtNum(pd) + " so'm / kun</div>" +
        '<div class="plan-feats">' +
        p.feats.map(function (f) { return "<span>" + f + "</span>"; }).join("") + "</div>" +
        '<button class="plan-go" type="button">' + svg("card") + "<span>" + p.cta + "</span></button>";
      var btn = card.querySelector(".plan-go");
      btn.onclick = function () { doSubscribe(p.key, btn); };
      c.appendChild(card);
    });
  }

  function openPaySheet(m) {
    haptic("sel");
    if (m && MODE_BENEFIT[m]) {
      el("payIcon").innerHTML = svg(MODE_ICON[m] || "ai");
      el("payTitle").textContent = (MODE_LABELS[m] || m) + " rejimi";
      el("payDesc").textContent = MODE_BENEFIT[m];
    } else {
      el("payIcon").innerHTML = svg("ai");
      el("payTitle").textContent = "Premium imkoniyatlar";
      el("payDesc").textContent =
        "Subtitr botdan to'liq foydalaning — tarjima, ikki qatlam, .srt fayl va sozlanadigan uslub bir obunada.";
    }
    var ul = el("payUnlocks"); ul.innerHTML = "";
    UNLOCKS.forEach(function (t) {
      var li = document.createElement("li");
      li.innerHTML = svg("check") + "<span>" + t + "</span>";
      ul.appendChild(li);
    });
    renderPlans();
    el("payErr").textContent = "";
    if (inTG) { try { tg.MainButton.hide(); } catch (e) {} }
    el("payOverlay").classList.add("open");
    el("payOverlay").setAttribute("aria-hidden", "false");
  }

  function closePaySheet() {
    el("payOverlay").classList.remove("open");
    el("payOverlay").setAttribute("aria-hidden", "true");
    if (inTG && state.section === "create") show(state.view);
  }

  function openExternal(url) {
    if (inTG) { try { tg.openLink(url); return; } catch (e) {} }
    window.open(url, "_blank");
  }

  function doSubscribe(plan, btn) {
    // To'lov sozlanmagan bo'lsa — bot obuna oqimiga yo'naltiramiz
    if (!state.payEnabled) { closePaySheet(); openBot("subscribe"); return; }
    btn.classList.add("loading");
    el("payErr").textContent = "";
    api("/api/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan: plan })
    }).then(function (r) {
      return r.json().then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (res) {
      btn.classList.remove("loading");
      if (!res.ok || !res.j.pay_url) {
        el("payErr").textContent = res.j.error || "Xatolik. Birozdan keyin urinib ko'ring.";
        return;
      }
      haptic("success");
      openExternal(res.j.pay_url);
    }).catch(function () {
      btn.classList.remove("loading");
      el("payErr").textContent = "Tarmoq xatosi. Qayta urinib ko'ring.";
    });
  }

  // ----------------------------------------------------------- donat modali
  var DON_PRESETS = [5000, 10000, 30000, 50000];

  function markDonChips() {
    var bs = el("donAmounts").querySelectorAll(".don-chip");
    for (var i = 0; i < bs.length; i++) {
      bs[i].classList.toggle("on", DON_PRESETS[i] === state.donAmount);
    }
  }

  function openDonate() {
    haptic("sel");
    state.donAmount = null;
    var c = el("donAmounts"); c.innerHTML = "";
    DON_PRESETS.forEach(function (a) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "don-chip";
      b.textContent = fmtNum(a) + " so'm";
      b.onclick = function () {
        haptic("sel"); state.donAmount = a; el("donCustom").value = ""; markDonChips();
      };
      c.appendChild(b);
    });
    el("donCustom").value = ""; el("donComment").value = ""; el("donErr").textContent = "";
    markDonChips();
    if (inTG) { try { tg.MainButton.hide(); } catch (e) {} }
    el("donOverlay").classList.add("open");
    el("donOverlay").setAttribute("aria-hidden", "false");
  }

  function closeDonate() {
    el("donOverlay").classList.remove("open");
    el("donOverlay").setAttribute("aria-hidden", "true");
    if (inTG && state.section === "create") show(state.view);
  }

  function doDonate() {
    var custom = parseInt((el("donCustom").value || "").replace(/\D/g, ""), 10);
    var amount = custom || state.donAmount || 0;
    if (!amount || amount < 1000) {
      el("donErr").textContent = "Minimal summa 1 000 so'm.";
      haptic("error");
      return;
    }
    if (!state.payEnabled) { closeDonate(); openBot("donate"); return; }
    var btn = el("donGo");
    btn.classList.add("loading");
    el("donErr").textContent = "";
    api("/api/donate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: amount, comment: (el("donComment").value || "").trim() })
    }).then(function (r) {
      return r.json().then(function (j) { return { ok: r.ok, j: j }; });
    }).then(function (res) {
      btn.classList.remove("loading");
      if (!res.ok || !res.j.pay_url) {
        el("donErr").textContent = res.j.error || "Xatolik. Qayta urinib ko'ring.";
        return;
      }
      haptic("success");
      openExternal(res.j.pay_url);
    }).catch(function () {
      btn.classList.remove("loading");
      el("donErr").textContent = "Tarmoq xatosi. Qayta urinib ko'ring.";
    });
  }

  function buildLangs() {
    var isTr = state.modes.some(function (m) { return TRANSLATE_MODES.indexOf(m) >= 0; });
    // Til tanlash faqat Tarjima va Ikki qatlam uchun kerak (tarjima tili).
    // Original / .srt — AI asl tilni AVTOMATIK aniqlaydi (xitoy, koreys,
    // hind... har qanday til o'z tilida mukammal yoziladi).
    if (!isTr) {
      state.lang = "auto";
      el("langLabel").style.display = "none";
      el("langSeg").style.display = "none";
      el("langSeg").innerHTML = "";
      return;
    }
    el("langLabel").style.display = "";
    el("langSeg").style.display = "";
    el("langLabel").textContent = "Tarjima tili";
    var order = TGT_ORDER;
    if (order.indexOf(state.lang) < 0) state.lang = order[0];
    var c = el("langSeg"); c.innerHTML = "";
    order.forEach(function (k) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = LANGS[k];
      if (k === state.lang) b.className = "on";
      b.onclick = function () { haptic("sel"); state.lang = k; buildLangs(); validate(); };
      c.appendChild(b);
    });
  }

  // ----------------------------------------------------------- manba
  function setMethod(m) {
    state.method = m;
    el("tabFile").classList.toggle("on", m === "file");
    el("tabUrl").classList.toggle("on", m === "url");
    el("fileArea").classList.toggle("hidden", m !== "file");
    el("urlArea").classList.toggle("hidden", m !== "url");
    validate();
  }

  var RING_C = 119.38;  // 2πr, r=19
  function setRing(pct) {
    var fg = el("ringFg");
    if (fg) fg.style.strokeDashoffset = String(RING_C * (1 - Math.max(0, Math.min(100, pct)) / 100));
    var pe = el("ringPct");
    if (pe) pe.textContent = Math.round(pct) + "%";
  }

  function setFile(f) {
    // Avvalgi staging bekor qilinadi
    if (state.stageXhr) { try { state.stageXhr.abort(); } catch (e) {} state.stageXhr = null; }
    state.file = f || null;
    state.stageId = null; state.staged = false; state.staging = false;
    state.pendingSubmit = false;
    var drop = el("drop");
    drop.classList.remove("staging", "staged");
    if (f) {
      drop.classList.add("has");
      el("dropText").textContent = f.name;
      startStaging(f);
    } else {
      drop.classList.remove("has");
      el("dropText").textContent = "Videoni tanlang yoki tashlang";
      el("dropHint").textContent = "MP4, MOV, MKV…";
    }
    validate();
  }

  function stageUpload(fd, onProgress) {
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      state.stageXhr = xhr;
      xhr.open("POST", "/api/stage");
      xhr.setRequestHeader("X-Init-Data", INIT);
      if (WEB_TOKEN) xhr.setRequestHeader("X-Web-Token", WEB_TOKEN);
      xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) onProgress(Math.round(e.loaded / e.total * 100));
      };
      xhr.onload = function () {
        state.stageXhr = null;
        var j = {};
        try { j = JSON.parse(xhr.responseText); } catch (e) {}
        resolve({ ok: xhr.status >= 200 && xhr.status < 300, j: j });
      };
      xhr.onerror = function () { state.stageXhr = null; reject(new Error("Yuklash uzildi (tarmoq)")); };
      xhr.onabort = function () { state.stageXhr = null; reject(new Error("abort")); };
      xhr.send(fd);
    });
  }

  function startStaging(f) {
    state.staging = true; state.staged = false;
    var drop = el("drop");
    drop.classList.add("staging"); drop.classList.remove("staged");
    el("dropHint").textContent = "Yuklanmoqda…";
    setRing(0);
    var fd = new FormData();
    fd.append("file", f);
    stageUpload(fd, function (pct) {
      setRing(pct);
      el("dropHint").textContent = pct < 100 ? "Yuklanmoqda… " + pct + "%" : "Tekshirilmoqda…";
    }).then(function (res) {
      state.staging = false;
      drop.classList.remove("staging");
      if (res.ok && res.j.stage_id) {
        state.staged = true; state.stageId = res.j.stage_id;
        drop.classList.add("staged");
        el("dropHint").textContent = "Yuklandi — tayyor ✓";
        haptic("success");
      } else {
        el("formErr").textContent = (res.j && res.j.error) || "Yuklash xatosi. Qayta tanlang.";
        haptic("error");
      }
      validate();
    }).catch(function (e) {
      state.staging = false;
      drop.classList.remove("staging");
      if (e && e.message === "abort") return;
      el("formErr").textContent = "Yuklash uzildi. Videoni qaytadan tanlang.";
      validate();
    });
  }

  function setGoText(label) {
    var b = el("goBtn");
    if (b && b.lastChild) b.lastChild.nodeValue = " " + label;
  }

  function validate() {
    var hasSrc = state.method === "file"
      ? state.staged
      : LINK_RE.test((el("url").value || "").trim());
    var ready = !state.busy && !state.staging && !!(hasSrc && state.modes.length && state.lang);
    // Yuklash payti: "Video yuklanmoqda…"; tugagach: "Subtitr yozish"
    var uploading = state.method === "file" && state.staging;
    var label = uploading ? "Video yuklanmoqda…" : "Subtitr yozish";
    if (inTG) {
      if (ready) tg.MainButton.enable(); else tg.MainButton.disable();
      try { tg.MainButton.setText(label); } catch (e) {}
    }
    setGoText(label);
    el("goBtn").disabled = !ready;
  }

  // ----------------------------------------------------------- yuborish
  function setProgMode(mode) {
    el("progBar").classList.toggle("hidden", mode !== "upload");
    if (mode === "upload") { el("progFill").style.width = "0%"; el("stepIc").innerHTML = svg("download"); }
  }

  function uploadFile(fd, onProgress) {
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/upload");
      xhr.setRequestHeader("X-Init-Data", INIT);
      if (WEB_TOKEN) xhr.setRequestHeader("X-Web-Token", WEB_TOKEN);
      xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) onProgress(Math.round(e.loaded / e.total * 100));
      };
      xhr.onload = function () {
        var j = {};
        try { j = JSON.parse(xhr.responseText); } catch (e) {}
        resolve({ ok: xhr.status >= 200 && xhr.status < 300, j: j });
      };
      xhr.onerror = function () { reject(new Error("Yuklash xatosi (tarmoq)")); };
      xhr.send(fd);
    });
  }

  function handleStart(res) {
    if (!res.ok) throw new Error(res.j.error || "Xatolik");
    state.jobId = res.j.job_id;
    el("progSub").textContent = "Iltimos kuting, oynani yopmang";
    poll(res.j.job_id);
  }

  function scrollToView() {
    try {
      var vp = el("viewPanel");
      if (vp && vp.scrollIntoView) vp.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {}
  }

  function submit() {
    if (state.busy) return;
    if (state.method === "file" && !state.staged) {
      el("formErr").textContent = state.staging
        ? "Video hali yuklanmoqda — biroz kuting."
        : "Avval videoni tanlang.";
      return;
    }
    runProcessing();
  }

  function runProcessing() {
    state.busy = true;
    show("progress");
    scrollToView();
    if (state.method === "file") {
      setProgMode("process");
      el("stepIc").innerHTML = svg("ai");
      el("progText").textContent = "Boshlanmoqda…";
      el("progSub").textContent = "Iltimos kuting, oynani yopmang";
      api("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage_id: state.stageId, modes: state.modes,
                               lang: state.lang, style: state.style })
      }).then(function (r) {
        return r.json().then(function (j) { return { ok: r.ok, j: j }; });
      }).then(handleStart).catch(function (e) { fail(e.message); });
    } else {
      setProgMode("process");
      el("stepIc").innerHTML = svg("link");
      el("progText").textContent = "Havola tekshirilmoqda…";
      var url = (el("url").value || "").trim();
      api("/api/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url, modes: state.modes, lang: state.lang, style: state.style })
      }).then(function (r) {
        return r.json().then(function (j) { return { ok: r.ok, j: j }; });
      }).then(handleStart).catch(function (e) { fail(e.message); });
    }
  }

  function stepIcon(msg) {
    var m = (msg || "").toLowerCase();
    if (/audio|ovoz|ajrat/.test(m)) return "audio";
    if (/tuzat|to'g'rila/.test(m)) return "edit";
    if (/tarjima/.test(m)) return "globe";
    if (/videoga|yozil|burn|biroz vaqt/.test(m)) return "film";
    if (/yuklab|havola|qabul/.test(m)) return "download";
    return "ai";
  }
  function cleanMsg(msg) {
    var t = (msg || "").replace(/^[^\p{L}\p{N}]+/u, "").trim();
    return t || "Qayta ishlanmoqda…";
  }
  function renderProgress(msg) {
    el("stepIc").innerHTML = svg(stepIcon(msg));
    el("progText").textContent = cleanMsg(msg);
  }

  function poll(jobId) {
    api("/api/status/" + jobId)
      .then(function (r) { return r.json(); })
      .then(function (s) {
        if (s.state === "done") { showResult(s); return; }
        if (s.state === "error") { fail(s.error || "Qayta ishlashda xatolik"); return; }
        if (s.state === "unknown") { fail("Job topilmadi"); return; }
        renderProgress(s.progress || "Qayta ishlanmoqda…");
        state.poll = setTimeout(function () { poll(jobId); }, 1500);
      })
      .catch(function () { state.poll = setTimeout(function () { poll(jobId); }, 2500); });
  }

  function withDlSuffix(u) { return u + (u.indexOf("?") >= 0 ? "&" : "?") + "dl=1"; }

  function showResult(s) {
    state.busy = false;
    var sb = el("sendChatBtn");
    if (sb) { sb.classList.remove("loading"); sb.disabled = false; sb.lastChild.nodeValue = " Chatga yuborish"; }
    var vid = el("resultVideo");
    var aud = el("resultAudio");
    var dl = el("dlBtn"), dl2 = el("dlBtn2");
    var badge = el("doneBadge");
    el("srtBox").classList.add("hidden");
    el("textBox").classList.add("hidden");
    el("multiBox").classList.add("hidden");
    if (aud) { aud.classList.add("hidden"); aud.removeAttribute("src"); aud.load(); }
    var modeLabelStr = state.modes.map(function (m) { return MODE_LABELS[m] || m; }).join(", ");

    // Ko'p rejim — natijalar ro'yxati
    if (s.kind === "multi") {
      vid.classList.add("hidden"); vid.removeAttribute("src"); vid.load();
      dl.classList.add("hidden"); dl2.classList.add("hidden");
      var rs = s.results || [];
      if (badge) badge.lastChild.nodeValue = " " + rs.length + " ta natija tayyor";
      var box = el("multiBox"); box.innerHTML = ""; box.classList.remove("hidden");
      rs.forEach(function (r) {
        var row = document.createElement("div"); row.className = "multi-row";
        row.innerHTML = '<span class="multi-lab"><span class="mi">' +
          svg(MODE_ICON[r.mode] || "type") + "</span>" + (MODE_LABELS[r.mode] || r.mode) + "</span>";
        var acts = document.createElement("span"); acts.className = "multi-acts";
        function addBtn(t, u) {
          var a = document.createElement("a"); a.className = "mbtn";
          a.href = withDlSuffix(u); a.setAttribute("download", ""); a.textContent = t;
          if (inTG) a.onclick = function (e) { e.preventDefault(); tg.openLink(withDlSuffix(u)); };
          acts.appendChild(a);
        }
        if (r.kind === "text" || r.kind === "vocab") { addBtn("PDF", r.pdf_url); addBtn(".txt", r.txt_url); }
        else if (r.kind === "srt") { addBtn(".srt", r.result_url); }
        else if (r.kind === "audio") { addBtn("MP3", r.result_url); }
        else { addBtn("Video", r.result_url); }
        row.appendChild(acts); box.appendChild(row);
      });
      addHistory({ dlUrl: "", kind: "multi", mode: state.modes.join(","),
        modeLabel: modeLabelStr,
        name: state.method === "file" ? (state.file && state.file.name) : "havola", ts: Date.now() });
      haptic("success"); show("result"); return;
    }

    dl.classList.remove("hidden");
    var isText = (s.kind === "text" || s.kind === "vocab");
    if (s.kind === "srt") {
      vid.classList.add("hidden"); vid.removeAttribute("src"); vid.load();
      el("srtBox").classList.remove("hidden");
    } else if (isText) {
      vid.classList.add("hidden"); vid.removeAttribute("src"); vid.load();
      el("textBox").classList.remove("hidden");
      el("textPreview").textContent = s.preview || "(bo'sh)";
    } else if (s.kind === "audio") {
      vid.classList.add("hidden"); vid.removeAttribute("src"); vid.load();
      if (aud) { aud.classList.remove("hidden"); aud.src = s.result_url; }
    } else {
      vid.classList.remove("hidden");
      vid.src = s.result_url;
    }
    if (badge) badge.lastChild.nodeValue =
      s.kind === "text" ? " Matn tayyor" :
      s.kind === "vocab" ? " Lug'at tayyor" :
      s.kind === "audio" ? " Audio tayyor" : " Subtitr tayyor";

    var primaryUrl;
    if (isText) {
      primaryUrl = withDlSuffix(s.pdf_url || s.result_url);
      dl.lastChild.nodeValue = " PDF yuklab olish";
      var txtUrl = withDlSuffix(s.txt_url || s.result_url);
      dl2.classList.remove("hidden");
      dl2.href = txtUrl;
      dl2.onclick = inTG ? function (e) { e.preventDefault(); tg.openLink(txtUrl); } : null;
    } else {
      primaryUrl = withDlSuffix(s.result_url);
      dl.lastChild.nodeValue =
        s.kind === "srt" ? " .srt yuklab olish" :
        s.kind === "audio" ? " MP3 yuklab olish" : " Videoni yuklab olish";
      dl2.classList.add("hidden");
    }
    dl.href = primaryUrl;
    dl.onclick = inTG ? function (e) { e.preventDefault(); tg.openLink(primaryUrl); } : null;
    addHistory({
      dlUrl: primaryUrl, kind: s.kind, mode: state.modes.join(","),
      modeLabel: modeLabelStr,
      name: state.method === "file" ? (state.file && state.file.name) : "havola",
      ts: Date.now()
    });
    haptic("success");
    show("result");
  }

  function sendToChat() {
    var btn = el("sendChatBtn");
    if (!state.jobId || btn.classList.contains("loading")) return;
    btn.classList.add("loading");
    var label = btn.lastChild;
    label.nodeValue = " Yuborilmoqda…";
    api("/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: state.jobId })
    }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        btn.classList.remove("loading");
        if (res.ok && res.j.ok) {
          label.nodeValue = " Chatga yuborildi ✓";
          btn.disabled = true;
          haptic("success");
        } else {
          label.nodeValue = " Chatga yuborish";
          el("formErr").textContent = (res.j && res.j.error) || "Yuborib bo'lmadi.";
          haptic("error");
        }
      }).catch(function () {
        btn.classList.remove("loading");
        label.nodeValue = " Chatga yuborish";
        haptic("error");
      });
  }

  function fail(msg) {
    state.busy = false;
    haptic("error");
    show("idle");
    el("formErr").textContent = msg;
    validate();
  }

  // ----------------------------------------------------------- ko'rinish
  function show(view) {
    state.view = view;
    el("idleView").classList.toggle("hidden", view !== "idle");
    el("progressView").classList.toggle("hidden", view !== "progress");
    el("resultView").classList.toggle("hidden", view !== "result");
    el("viewPanel").classList.toggle("active", view !== "idle");
    if (inTG && state.section === "create") {
      if (view === "progress") { tg.BackButton.hide(); tg.MainButton.hide(); }
      else if (view === "result") { tg.MainButton.hide(); tg.BackButton.show(); }
      else { tg.BackButton.hide(); tg.MainButton.show(); validate(); }
    }
  }

  function reset() {
    if (state.poll) clearTimeout(state.poll);
    state.busy = false;
    setFile(null);
    el("file").value = "";
    el("url").value = "";
    var vid = el("resultVideo");
    vid.removeAttribute("src"); vid.load();
    show("idle");
    loadProfile();
  }

  // Shu videodan boshqa format — videoni QAYTA YUKLAMASDAN formaga qaytamiz
  // (staged video saqlangan). Foydalanuvchi yangi rejim tanlab, tugmani bossin.
  function anotherFormat() {
    if (state.poll) clearTimeout(state.poll);
    state.busy = false;
    state.jobId = null;
    el("formErr").textContent = "";
    var vid = el("resultVideo");
    vid.removeAttribute("src"); vid.load();
    show("idle");
    haptic("sel");
    try {
      var seg = el("modeSeg");
      if (seg && seg.scrollIntoView) seg.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (e) {}
    validate();
  }

  // ----------------------------------------------------------- bo'limlar
  function setSection(name) {
    state.section = name;
    ["create", "style", "history", "profile"].forEach(function (s) {
      el("sec-" + s).classList.toggle("hidden", s !== name);
    });
    var btns = document.querySelectorAll(".snav-b");
    for (var i = 0; i < btns.length; i++) {
      btns[i].classList.toggle("on", btns[i].getAttribute("data-sec") === name);
    }
    if (name === "history") renderHistory();
    if (name === "profile") loadDonors();
    if (inTG) {
      if (name === "create") show(state.view);
      else { tg.MainButton.hide(); tg.BackButton.hide(); }
    }
    haptic("sel");
  }

  // ----------------------------------------------------------- tarix
  function loadHistory() { try { return JSON.parse(localStorage.getItem(HIST_KEY) || "[]"); } catch (e) { return []; } }
  function addHistory(item) {
    var a = loadHistory(); a.unshift(item);
    try { localStorage.setItem(HIST_KEY, JSON.stringify(a.slice(0, 20))); } catch (e) {}
  }
  function renderHistory() {
    var a = loadHistory(), list = el("historyList");
    list.innerHTML = "";
    el("historyEmpty").classList.toggle("hidden", a.length > 0);
    a.forEach(function (it) {
      var d = new Date(it.ts);
      var when = ("0" + d.getDate()).slice(-2) + "." + ("0" + (d.getMonth() + 1)).slice(-2) +
        " " + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2);
      var card = document.createElement("div");
      card.className = "hist-card";
      card.innerHTML =
        '<div class="hist-ic">' + svg(it.kind === "srt" ? "file" : it.kind === "audio" ? "audio" : "film") + "</div>" +
        '<div class="hist-info"><div class="hist-mode">' + escapeHtml(it.modeLabel || it.mode) +
        '</div><div class="hist-meta">' + when + (it.name ? " · " + escapeHtml(it.name) : "") + "</div></div>" +
        '<a class="hist-dl" href="' + it.dlUrl + '" download title="Yuklab olish">' + svg("download") + "</a>";
      var dl = card.querySelector(".hist-dl");
      if (inTG) dl.onclick = function (e) { e.preventDefault(); tg.openLink(it.dlUrl); };
      list.appendChild(card);
    });
  }

  // ----------------------------------------------------------- uslub
  function loadStyle() {
    try { return Object.assign({}, STYLE_DEFAULTS, JSON.parse(localStorage.getItem(STYLE_KEY) || "{}")); }
    catch (e) { return Object.assign({}, STYLE_DEFAULTS); }
  }
  function saveStyle() { try { localStorage.setItem(STYLE_KEY, JSON.stringify(state.style)); } catch (e) {} }
  function outlineShadow(c) {
    return ["-1.2px -1.2px 0 " + c, "1.2px -1.2px 0 " + c, "-1.2px 1.2px 0 " + c,
      "1.2px 1.2px 0 " + c, "0 0 2px " + c].join(",");
  }
  function applyPreview() {
    var s = state.style;
    el("prevFrame").className = "preview-frame pos-" + s.position;
    var sub = el("prevSub");
    sub.className = "preview-sub" + (s.box ? " box" : "");
    sub.style.fontSize = SIZE_PX[s.font_size] + "px";
    sub.style.fontWeight = s.bold ? "700" : "500";
    var sh = outlineShadow(s.outline_color);
    sub.innerHTML =
      '<span class="pline" style="color:' + s.text_color + ';text-shadow:' + sh + '">Salom, dunyo!</span><br>' +
      '<span class="pline" style="color:' + s.trans_color + ';text-shadow:' + sh + '">Hello, world!</span>';
  }
  function setSeg(segId, val) {
    var bs = el(segId).querySelectorAll("button");
    for (var i = 0; i < bs.length; i++) bs[i].classList.toggle("on", bs[i].getAttribute("data-v") === val);
  }
  function setStyleControls() {
    el("cText").value = state.style.text_color;
    el("cOutline").value = state.style.outline_color;
    el("cTrans").value = state.style.trans_color;
    el("tBold").checked = state.style.bold;
    el("tBox").checked = state.style.box;
    setSeg("sizeSeg", state.style.font_size);
    setSeg("posSeg", state.style.position);
  }
  function styleChanged() { applyPreview(); saveStyle(); }
  function bindSeg(segId, key) {
    var bs = el(segId).querySelectorAll("button");
    for (var i = 0; i < bs.length; i++) {
      (function (b) {
        b.onclick = function () {
          haptic("sel"); state.style[key] = b.getAttribute("data-v");
          setSeg(segId, state.style[key]); styleChanged();
        };
      })(bs[i]);
    }
  }
  function initStyle() {
    state.style = loadStyle();
    setStyleControls();
    applyPreview();
    el("cText").oninput = function () { state.style.text_color = this.value; styleChanged(); };
    el("cOutline").oninput = function () { state.style.outline_color = this.value; styleChanged(); };
    el("cTrans").oninput = function () { state.style.trans_color = this.value; styleChanged(); };
    el("tBold").onchange = function () { state.style.bold = this.checked; styleChanged(); };
    el("tBox").onchange = function () { state.style.box = this.checked; styleChanged(); };
    bindSeg("sizeSeg", "font_size");
    bindSeg("posSeg", "position");
    el("styleSave").onclick = function () { saveStyle(); haptic("success"); setSection("create"); };
    el("styleReset").onclick = function () {
      state.style = Object.assign({}, STYLE_DEFAULTS); setStyleControls(); styleChanged(); haptic("sel");
    };
    el("styleSubBtn").onclick = function () { openPaySheet(null); };
  }

  // ----------------------------------------------------------- bot havolasi
  function openBot(payload) {
    if (!state.botUser) return;
    var link = "https://t.me/" + state.botUser + (payload ? "?start=" + payload : "");
    if (inTG) tg.openTelegramLink(link); else window.open(link, "_blank");
  }

  // ----------------------------------------------------------- hodisalar
  el("tabFile").addEventListener("click", function () { setMethod("file"); });
  el("tabUrl").addEventListener("click", function () { setMethod("url"); });
  el("file").addEventListener("change", function (e) {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  });
  el("url").addEventListener("input", validate);
  var drop = el("drop");
  ["dragenter", "dragover"].forEach(function (ev) {
    drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("over"); });
  });
  ["dragleave", "drop"].forEach(function (ev) {
    drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("over"); });
  });
  drop.addEventListener("drop", function (e) {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  });
  el("goBtn").addEventListener("click", submit);
  el("againBtn").addEventListener("click", reset);
  el("anotherBtn").addEventListener("click", anotherFormat);
  el("sendChatBtn").addEventListener("click", sendToChat);
  el("headerUser").addEventListener("click", function () { setSection("profile"); });
  el("webBtn").addEventListener("click", openInBrowser);
  // "Brauzerda ochish" faqat Telegram ichida mantiqiy (brauzerда allaqachon brauzer)
  if (!inTG) el("webBtn").classList.add("hidden");
  el("subBtn").addEventListener("click", function () { openPaySheet(null); });
  el("donateBtn").addEventListener("click", openDonate);

  el("payClose").addEventListener("click", closePaySheet);
  el("payOverlay").addEventListener("click", function (e) {
    if (e.target === el("payOverlay")) closePaySheet();
  });

  el("donClose").addEventListener("click", closeDonate);
  el("donOverlay").addEventListener("click", function (e) {
    if (e.target === el("donOverlay")) closeDonate();
  });
  el("donGo").addEventListener("click", doDonate);
  el("donCustom").addEventListener("input", function () {
    state.donAmount = null; markDonChips();
  });

  var navBtns = document.querySelectorAll(".snav-b");
  for (var i = 0; i < navBtns.length; i++) {
    navBtns[i].addEventListener("click", function () { setSection(this.getAttribute("data-sec")); });
  }

  if (inTG) {
    el("goBtn").style.display = "none";
    try {
      tg.MainButton.setText("Subtitr yozish");
      tg.MainButton.onClick(submit);
      tg.BackButton.onClick(reset);
      tg.MainButton.show();
    } catch (e) {}
  }

  initStyle();
  show("idle");
  loadProfile();
})();
