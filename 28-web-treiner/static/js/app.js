const appRoot = document.querySelector("#app");
const storageKey = "train.shamsiyev.uz.completed.v1";
const isExercisePage = appRoot.dataset.page === "exercise";

const state = {
  tracks: [],
  exercises: [],
  activeTrack: "all",
  activeId: null,
  answers: {},
  feedback: {},
  completed: new Set(),
  timerId: null,
  remainingSeconds: {},
  recordingId: null,
  speakingId: null,
};

const icons = {
  microphone:
    '<svg class="icon icon-mic" viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="2.5" width="6" height="12" rx="3"></rect><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3.5M8.5 21.5h7"></path></svg>',
  sound:
    '<svg class="icon icon-sound" viewBox="0 0 24 24" aria-hidden="true"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>',
  code:
    '<svg class="icon icon-code" viewBox="0 0 24 24" aria-hidden="true"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
  play:
    '<svg class="icon icon-play" viewBox="0 0 24 24" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>',
  arrow:
    '<svg class="icon icon-arrow" viewBox="0 0 24 24" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>',
  back:
    '<svg class="icon icon-back" viewBox="0 0 24 24" aria-hidden="true"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>',
};

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function highlightCode(rawCode = "") {
  if (!rawCode) return "";
  let esc = escapeHtml(rawCode);
  esc = esc.replace(/(@[a-zA-Z0-9_\.]+)/g, '<span class="tok-decorator">$1</span>');
  esc = esc.replace(/\b(async|def|return|await|yield|with|class|from|import)\b/g, '<span class="tok-keyword">$1</span>');
  esc = esc.replace(/(&#039;.*?&#039;|&quot;.*?&quot;)/g, '<span class="tok-string">$1</span>');
  esc = esc.replace(/(___)/g, '<span class="tok-blank">$1</span>');
  return esc;
}

function trackFor(id) {
  return state.tracks.find((track) => track.id === id);
}

function activeExercise() {
  return state.exercises.find((exercise) => exercise.id === state.activeId) || state.exercises[0];
}

function filteredExercises() {
  if (state.activeTrack === "all") return state.exercises;
  return state.exercises.filter((exercise) => exercise.track_id === state.activeTrack);
}

function exerciseUrl(exerciseId) {
  return `/mashq/${encodeURIComponent(exerciseId)}`;
}

function typeLabel(kind) {
  const labels = {
    pronunciation: "Talaffuz",
    listening_number: "Listening",
    code_challenge: "Kod challenge",
  };
  return labels[kind] || "Mashq";
}

function typeIcon(kind) {
  if (kind === "pronunciation") return icons.microphone;
  if (kind === "listening_number") return icons.sound;
  return icons.code;
}

function formatTimer(seconds) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

function loadCompleted() {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || "[]");
    if (Array.isArray(saved)) state.completed = new Set(saved);
  } catch {
    state.completed = new Set();
  }
}

function saveCompleted() {
  localStorage.setItem(storageKey, JSON.stringify([...state.completed]));
}

function topTrackButtons() {
  const allButton = { id: "all", title: "Barchasi", accent: "all" };
  return [allButton, ...state.tracks]
    .map((track) => {
      const count =
        track.id === "all"
          ? state.exercises.length
          : state.exercises.filter((e) => e.track_id === track.id).length;
      const isActive = state.activeTrack === track.id;
      return `
        <button class="top-track-button ${isActive ? "active" : ""}" data-action="select-track" data-track="${track.id}" type="button" aria-pressed="${isActive}">
          <span class="top-track-marker ${track.accent || ""}"></span>
          <span class="top-track-label">${escapeHtml(track.title)}</span>
          <span class="top-track-count">${count}</span>
        </button>
      `;
    })
    .join("");
}

function exerciseCard(exercise, index) {
  const track = trackFor(exercise.track_id);
  const accent = track?.accent || "mint";
  const completed = state.completed.has(exercise.id);
  return `
    <a class="exercise-card track-${accent}" data-track="${exercise.track_id}" data-accent="${accent}" href="${exerciseUrl(exercise.id)}" ${completed ? 'data-completed="true"' : ""}>
      <div class="card-glow" aria-hidden="true"></div>
      <span class="card-topline">
        <span class="card-badges">
          <span class="exercise-number">#${String(index + 1).padStart(2, "0")}</span>
          <span class="track-pill ${accent}">${escapeHtml(track?.title || "")}</span>
        </span>
        <span class="exercise-kind-icon ${accent}" title="${escapeHtml(typeLabel(exercise.kind))}">
          ${typeIcon(exercise.kind)}
        </span>
      </span>
      <h2>${escapeHtml(exercise.title)}</h2>
      <p>${escapeHtml(exercise.description)}</p>
      <span class="card-meta">
        <span class="meta-duration">
          <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          ${exercise.duration_minutes} daqiqa
        </span>
        <span class="card-action ${completed ? "is-completed" : ""}">
          ${completed ? '<span class="completed-label"><svg class="icon icon-check" viewBox="0 0 24 24" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>Bajarildi</span>' : `<span>Boshlash</span> ${icons.arrow}`}
        </span>
      </span>
    </a>
  `;
}

function feedbackMarkup(exerciseId) {
  const feedback = state.feedback[exerciseId];
  if (!feedback) return "";
  const isCorrect = Boolean(feedback.correct);
  const isError = !isCorrect && (feedback.type === "error" || feedback.correct === false);
  const style = isCorrect ? "correct" : isError ? "incorrect" : "info";
  const icon = isCorrect
    ? '<svg class="feedback-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><polyline points="16 9 10 15 7 12"></polyline></svg>'
    : isError
      ? '<svg class="feedback-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
      : '<svg class="feedback-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';

  return `
    <div class="feedback ${style}" role="status">
      ${icon}
      <div class="feedback-content">
        <span class="feedback-heading">${isCorrect ? "Barakalla! To'g'ri natija" : isError ? "Natija xato bo'ldi" : "Eslatma"}</span>
        <span class="feedback-message">${escapeHtml(feedback.message)}</span>
      </div>
    </div>
  `;
}

function practiceBody(exercise) {
  const answer = escapeHtml(state.answers[exercise.id] || "");

  if (exercise.kind === "pronunciation") {
    const recording = state.recordingId === exercise.id;
    return `
      <div class="speech-challenge-card ${recording ? "is-recording" : ""}">
        <div class="challenge-header">
          <span class="challenge-type-badge">
            ${icons.microphone}
            <span>Nutq artikulyatsiyasi</span>
          </span>
          <span class="lang-tag">RU</span>
        </div>
        <div class="phrase-quote-wrap">
          <p class="target-phrase" lang="ru">${escapeHtml(exercise.target_text)}</p>
        </div>
        <div class="exercise-actions">
          <button class="button ${recording ? "button-recording" : "button-secondary"}" data-action="record" data-exercise="${exercise.id}" type="button">
            ${icons.microphone}
            <span>${recording ? "Tinglanmoqda (gapiring)..." : "Mikrofon orqali yozish"}</span>
            ${recording ? '<span class="recording-pulse"></span>' : ""}
          </button>
        </div>
      </div>
      <div class="answer-wrapper">
        <label class="input-label" for="ans-in-${exercise.id}">Tinglangan yoki kiritilgan matn:</label>
        <div class="answer-line">
          <input id="ans-in-${exercise.id}" class="answer-input" data-answer-input="${exercise.id}" type="text" lang="ru" value="${answer}" placeholder="Aytilgan matn shu yerda aks etadi..." autocomplete="off" />
          <button class="button button-primary" data-action="submit-answer" data-exercise="${exercise.id}" type="button">Tekshirish</button>
        </div>
      </div>
      ${feedbackMarkup(exercise.id)}
    `;
  }

  if (exercise.kind === "listening_number") {
    const isSpeaking = state.speakingId === exercise.id;
    return `
      <div class="audio-challenge-card ${isSpeaking ? "is-speaking" : ""}">
        <div class="challenge-header">
          <span class="challenge-type-badge">
            ${icons.sound}
            <span>Inglizcha sonni eshitish</span>
          </span>
          <span class="lang-tag">EN</span>
        </div>
        <div class="sound-wave-box ${isSpeaking ? "wave-active" : ""}" aria-hidden="true">
          <span class="bar bar-1"></span>
          <span class="bar bar-2"></span>
          <span class="bar bar-3"></span>
          <span class="bar bar-4"></span>
          <span class="bar bar-5"></span>
          <span class="bar bar-6"></span>
          <span class="bar bar-7"></span>
        </div>
        <div class="exercise-actions audio-action-center">
          <button class="button button-primary button-listen" data-action="speak" data-exercise="${exercise.id}" type="button">
            ${icons.sound}
            <span>${isSpeaking ? "Ovoz yangramoqda..." : "Sonni tinglash"}</span>
          </button>
        </div>
      </div>
      <div class="answer-wrapper">
        <label class="input-label" for="ans-in-${exercise.id}">Eshitilgan sonni raqam shaklida kiriting:</label>
        <div class="answer-line">
          <input id="ans-in-${exercise.id}" class="answer-input answer-input-number" data-answer-input="${exercise.id}" type="text" inputmode="numeric" value="${answer}" placeholder="Masalan: 48" autocomplete="off" />
          <button class="button button-secondary" data-action="submit-answer" data-exercise="${exercise.id}" type="button">Tekshirish</button>
        </div>
      </div>
      ${feedbackMarkup(exercise.id)}
    `;
  }

  const choices = exercise.choices
    .map(
      (choice, idx) => `
        <button class="choice-button ${state.answers[exercise.id] === choice.value ? "active" : ""}" data-action="select-choice" data-exercise="${exercise.id}" data-value="${escapeHtml(choice.value)}" type="button">
          <span class="choice-badge">${String.fromCharCode(65 + idx)}</span>
          <div class="choice-text-col">
            <span class="choice-value">${escapeHtml(choice.value)}</span>
            ${choice.label && choice.label !== choice.value ? `<span class="choice-label">${escapeHtml(choice.label)}</span>` : ""}
          </div>
        </button>
      `,
    )
    .join("");

  return `
    <div class="code-challenge-window">
      <div class="code-window-header">
        <div class="window-controls">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
        </div>
        <span class="window-title">fastapi_exercise.py</span>
        <span class="window-lang">Python 3.12</span>
      </div>
      <pre class="code-block"><code>${highlightCode(exercise.code)}</code></pre>
    </div>
    <div class="choice-section">
      <span class="choice-prompt">To'g'ri variantni tanlang:</span>
      <div class="choice-list">${choices}</div>
    </div>
    <div class="exercise-actions">
      <button class="button button-primary submit-code-btn" data-action="submit-answer" data-exercise="${exercise.id}" type="button">
        Javobni tekshirish ${icons.arrow}
      </button>
    </div>
    ${feedbackMarkup(exercise.id)}
  `;
}

function practicePanel(exercise, showOverview = true) {
  const remaining = state.remainingSeconds[exercise.id] ?? exercise.duration_minutes * 60;
  const isTimerRunning = Boolean(state.timerId);
  return `
    <section class="practice-panel" id="practice-panel" aria-labelledby="${showOverview ? "practice-title" : "exercise-title"}">
      <div class="practice-content">
        ${
          showOverview
            ? `
              <p class="panel-kicker">${escapeHtml(typeLabel(exercise.kind))} / ${escapeHtml(exercise.level)}</p>
              <div class="practice-title-row">
                <h2 id="practice-title">${escapeHtml(exercise.title)}</h2>
                <time class="timer" id="exercise-timer" datetime="PT${remaining}S">${formatTimer(remaining)}</time>
              </div>
              <p class="instruction">${escapeHtml(exercise.instruction)}</p>
            `
            : ""
        }
        <div class="practice-body">${practiceBody(exercise)}</div>
      </div>
      <aside class="practice-aside" aria-label="Mashq yo'riqnomasi">
        <div class="aside-info-group">
          <div class="aside-block">
            <span class="aside-group-title">Vazifa tavsifi</span>
            <p class="aside-description">${escapeHtml(exercise.description)}</p>
          </div>
          ${
            exercise.hint
              ? `
              <div class="hint">
                <span class="hint-header">
                  <svg class="hint-icon" viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                  </svg>
                  <strong>Diqqat nuqtasi</strong>
                </span>
                <p class="hint-text">${escapeHtml(exercise.hint)}</p>
              </div>
            `
              : ""
          }
        </div>
        <div class="aside-timer-box">
          <button class="button button-secondary timer-start ${isTimerRunning ? "is-running" : ""}" data-action="start-timer" data-exercise="${exercise.id}" type="button">
            ${isTimerRunning ? '<span class="timer-live-dot"></span>' : icons.play}
            <span>${isTimerRunning ? "Taymer ishlamoqda" : "Taymerni boshlash"}</span>
          </button>
          <span class="timer-hint">Belgilangan vaqt ichida yakunlang</span>
        </div>
      </aside>
    </section>
  `;
}

function renderCatalog() {
  const exercises = filteredExercises();
  const currentTrack = trackFor(state.activeTrack);
  const title = state.activeTrack === "all" ? "Barcha mashqlar" : currentTrack?.title || "Mashqlar";
  const completedCount = state.exercises.filter((e) => state.completed.has(e.id)).length;
  const totalCount = state.exercises.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  appRoot.innerHTML = `
    <div class="app-shell" data-active-track="${state.activeTrack}">
      <header class="topbar">
        <div class="topbar-inner">
          <div class="brand">
            <a class="brand-link" href="/" aria-label="train.shamsiyev.uz asosiy sahifa">
              <span class="brand-icon-wrap">
                <svg class="brand-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor"/>
                </svg>
              </span>
              <span class="brand-name">train<span class="brand-dot">.</span><span class="brand-sub">shamsiyev.uz</span></span>
            </a>
            <span class="brand-badge">Trenajyor</span>
          </div>
          <nav class="top-trackbar" aria-label="Yo'nalishlar">${topTrackButtons()}</nav>
        </div>
      </header>
      <main id="main-content">
        <section class="hero-banner">
          <div class="hero-content">
            <span class="hero-eyebrow">
              <span class="pulse-dot"></span>
              Qisqa va maqsadli amaliyot
            </span>
            <h1 class="hero-title">Til va backend bo'yicha<br/><span class="hero-gradient">aniq intervalli mashqlar</span></h1>
            <p class="hero-subtitle">Har kuni 5-10 daqiqa: ravon talaffuz, listening anglash va FastAPI backend reflekslarini mustahkamlang.</p>
          </div>
          <div class="progress-card">
            <div class="progress-top">
              <span class="progress-label">Umumiy progress</span>
              <span class="progress-stats"><strong>${completedCount}</strong> / ${totalCount} mashq</span>
            </div>
            <div class="progress-bar-bg" role="progressbar" aria-valuenow="${progressPercent}" aria-valuemin="0" aria-valuemax="100" aria-label="Mashqlar progressi">
              <div class="progress-bar-fill" style="width: ${progressPercent}%;"></div>
            </div>
            <div class="progress-bottom">
              <span class="progress-sub">${progressPercent === 100 ? "Ajoyib! Barcha mashqlar bajarildi." : "Doimiy takrorlash mahorat garovidir."}</span>
              <span class="progress-pct">${progressPercent}%</span>
            </div>
          </div>
        </section>

        <section class="exercise-zone" aria-labelledby="exercise-list-title">
          <div class="section-heading">
            <div class="section-heading-text">
              <h2 id="exercise-list-title">${escapeHtml(title)}</h2>
              <p class="section-desc">${escapeHtml(currentTrack?.description || "Barcha yo'nalishlar bo'yicha intensiv mashqlar to'plami.")}</p>
            </div>
            <span class="exercise-count">${String(exercises.length).padStart(2, "0")} ta mashq</span>
          </div>
          ${exercises.length ? `<div class="exercise-grid">${exercises.map(exerciseCard).join("")}</div>` : '<p class="empty-state">Bu yo\'nalishda hozircha mashq yo\'q.</p>'}
        </section>
      </main>
    </div>
  `;
}

function renderExercisePage() {
  const exercise = activeExercise();
  if (!exercise) {
    renderError("Mashq topilmadi.");
    return;
  }

  const track = trackFor(exercise.track_id);
  const accent = track?.accent || "mint";
  const remaining = state.remainingSeconds[exercise.id] ?? exercise.duration_minutes * 60;
  const completed = state.completed.has(exercise.id);

  appRoot.innerHTML = `
    <div class="app-shell exercise-page" data-accent="${accent}" data-track="${exercise.track_id}">
      <header class="topbar detail-topbar">
        <a class="back-link" href="/">
          ${icons.back}
          <span>Barcha mashqlar</span>
        </a>
        <div class="detail-topbar-right">
          <span class="detail-track-badge ${accent}">
            <span class="track-dot ${accent}"></span>
            <span class="detail-track">${escapeHtml(track?.title || typeLabel(exercise.kind))}</span>
          </span>
          ${completed ? '<span class="status-pill completed"><svg class="icon icon-check" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg> Bajarildi</span>' : ""}
        </div>
      </header>
      <main id="main-content">
        <section class="exercise-zone exercise-detail-zone" aria-labelledby="exercise-title">
          <div class="detail-header-card">
            <div class="panel-meta-row">
              <span class="panel-kicker">${escapeHtml(typeLabel(exercise.kind))} / ${escapeHtml(exercise.level)}</span>
              <span class="detail-duration-chip">
                <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                ${exercise.duration_minutes} daqiqa
              </span>
            </div>
            <div class="detail-title-row">
              <h1 id="exercise-title">${escapeHtml(exercise.title)}</h1>
              <div class="timer-box">
                <span class="timer-caption">Qolgan vaqt</span>
                <time class="timer" id="exercise-timer" datetime="PT${remaining}S">${formatTimer(remaining)}</time>
              </div>
            </div>
            <p class="instruction detail-instruction">${escapeHtml(exercise.instruction)}</p>
          </div>
          ${practicePanel(exercise, false)}
        </section>
      </main>
    </div>
  `;
}

function renderError(message) {
  appRoot.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <div class="topbar-inner">
          <div class="brand">
            <a class="brand-link" href="/">
              <span class="brand-icon-wrap">
                <svg class="brand-icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor"/>
                </svg>
              </span>
              <span class="brand-name">train<span class="brand-dot">.</span><span class="brand-sub">shamsiyev.uz</span></span>
            </a>
          </div>
        </div>
      </header>
      <main id="main-content">
        <div class="error-state-card">
          <div class="error-icon">!</div>
          <h2>Xatolik yuz berdi</h2>
          <p class="error-state">${escapeHtml(message)}</p>
          <a class="button button-primary" href="/">Bosh sahifaga qaytish</a>
        </div>
      </main>
    </div>
  `;
}

function renderCurrentPage() {
  if (isExercisePage) renderExercisePage();
  else renderCatalog();
}

function updateTimer() {
  const exercise = activeExercise();
  const timer = document.querySelector("#exercise-timer");
  if (!exercise || !timer) return;

  const seconds = state.remainingSeconds[exercise.id] ?? exercise.duration_minutes * 60;
  timer.textContent = formatTimer(seconds);
  timer.dateTime = `PT${seconds}S`;
}

function startTimer(exerciseId) {
  if (state.timerId) return;
  const exercise = state.exercises.find((item) => item.id === exerciseId);
  if (!exercise) return;

  state.remainingSeconds[exerciseId] ??= exercise.duration_minutes * 60;
  renderCurrentPage();

  state.timerId = window.setInterval(() => {
    state.remainingSeconds[exerciseId] = Math.max(0, state.remainingSeconds[exerciseId] - 1);
    updateTimer();
    if (state.remainingSeconds[exerciseId] === 0) {
      window.clearInterval(state.timerId);
      state.timerId = null;
      state.feedback[exerciseId] = { type: "info", message: "Sikl tugadi. Natijani tekshirib, keyingi mashqqa o'ting." };
      renderCurrentPage();
    }
  }, 1000);
}

function speak(exercise) {
  if (!("speechSynthesis" in window) || !exercise.audio_text) {
    state.feedback[exercise.id] = { type: "error", message: "Bu brauzerda ovozli tinglash mavjud emas." };
    renderCurrentPage();
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(exercise.audio_text);
  utterance.lang = "en-US";
  utterance.rate = 0.83;
  state.speakingId = exercise.id;
  renderCurrentPage();

  utterance.onend = () => {
    state.speakingId = null;
    renderCurrentPage();
  };
  utterance.onerror = () => {
    state.speakingId = null;
    renderCurrentPage();
  };
  window.speechSynthesis.speak(utterance);
}

function recordPronunciation(exercise) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    state.feedback[exercise.id] = { type: "error", message: "Ovozli yozuv bu brauzerda qo'llab-quvvatlanmaydi. Matnni qo'lda kiriting." };
    renderCurrentPage();
    return;
  }

  const recognition = new Recognition();
  recognition.lang = "ru-RU";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  state.recordingId = exercise.id;
  renderCurrentPage();

  recognition.onresult = (event) => {
    state.answers[exercise.id] = event.results[0][0].transcript;
    state.recordingId = null;
    renderCurrentPage();
  };
  recognition.onerror = () => {
    state.recordingId = null;
    state.feedback[exercise.id] = { type: "error", message: "Ovoz aniqlanmadi. Yana urinib ko'ring yoki matnni kiriting." };
    renderCurrentPage();
  };
  recognition.onend = () => {
    if (state.recordingId === exercise.id) {
      state.recordingId = null;
      renderCurrentPage();
    }
  };
  recognition.start();
}

async function submitAnswer(exercise) {
  const answer = state.answers[exercise.id]?.trim();
  if (!answer) {
    state.feedback[exercise.id] = { type: "info", message: "Avval javobni kiriting yoki variantni tanlang." };
    renderCurrentPage();
    return;
  }

  try {
    const response = await fetch(`/api/exercises/${encodeURIComponent(exercise.id)}/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    if (!response.ok) throw new Error("Tekshiruvda xatolik yuz berdi.");

    const result = await response.json();
    state.feedback[exercise.id] = { ...result, type: result.correct ? "success" : "error" };
    if (result.correct) {
      state.completed.add(exercise.id);
      saveCompleted();
    }
  } catch {
    state.feedback[exercise.id] = { type: "error", message: "Tekshiruvni yakunlab bo'lmadi. Ulanishni tekshiring." };
  }
  renderCurrentPage();
}

appRoot.addEventListener("input", (event) => {
  const input = event.target.closest("[data-answer-input]");
  if (input) state.answers[input.dataset.answerInput] = input.value;
});

appRoot.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  const action = button.dataset.action;
  if (action === "select-track") {
    state.activeTrack = button.dataset.track;
    renderCatalog();
    return;
  }

  const exercise = state.exercises.find((item) => item.id === button.dataset.exercise);
  if (!exercise) return;

  if (action === "select-choice") {
    state.answers[exercise.id] = button.dataset.value;
    renderCurrentPage();
  }
  if (action === "submit-answer") submitAnswer(exercise);
  if (action === "start-timer") startTimer(exercise.id);
  if (action === "speak") speak(exercise);
  if (action === "record") recordPronunciation(exercise);
});

async function initialize() {
  try {
    const tracksResponse = await fetch("/api/tracks");
    if (!tracksResponse.ok) throw new Error("catalog unavailable");
    state.tracks = await tracksResponse.json();

    if (isExercisePage) {
      const exerciseId = appRoot.dataset.exerciseId;
      const exerciseResponse = await fetch(`/api/exercises/${encodeURIComponent(exerciseId)}`);
      if (!exerciseResponse.ok) throw new Error("exercise unavailable");
      const exercise = await exerciseResponse.json();
      state.exercises = [exercise];
      state.activeId = exercise.id;
    } else {
      const exercisesResponse = await fetch("/api/exercises");
      if (!exercisesResponse.ok) throw new Error("catalog unavailable");
      state.exercises = await exercisesResponse.json();
    }

    loadCompleted();
    renderCurrentPage();
  } catch {
    renderError(isExercisePage ? "Mashqni yuklab bo'lmadi. Sahifani yangilab ko'ring." : "Mashqlarni yuklab bo'lmadi. Sahifani yangilab ko'ring.");
  }
}

initialize();
