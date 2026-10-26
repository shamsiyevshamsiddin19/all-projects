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
};

const icons = {
  microphone:
    '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="2.5" width="6" height="12" rx="3"></rect><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3.5M8.5 21.5h7"></path></svg>',
  sound:
    '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9.5v5h3.5l4 3.5V6l-4 3.5H4Z"></path><path d="M15.5 9a4.3 4.3 0 0 1 0 6M18.2 6.4a8.1 8.1 0 0 1 0 11.2"></path></svg>',
  code:
    '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m8.5 7-5 5 5 5M15.5 7l5 5-5 5M14 4.5 10 19.5"></path></svg>',
  play:
    '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 10 7-10 7V5Z"></path></svg>',
  arrow:
    '<svg class="icon icon-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M14 7l5 5-5 5"></path></svg>',
  back:
    '<svg class="icon icon-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H6M10 7l-5 5 5 5"></path></svg>',
};

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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
    code_challenge: "Kod",
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
  const allButton = { id: "all", title: "Barchasi", accent: "" };
  return [allButton, ...state.tracks]
    .map(
      (track) => `
        <button class="top-track-button ${state.activeTrack === track.id ? "active" : ""}" data-action="select-track" data-track="${track.id}" type="button" aria-pressed="${state.activeTrack === track.id}">
          <span class="top-track-marker ${track.accent || ""}"></span>
          <span class="top-track-label">${escapeHtml(track.title)}</span>
        </button>
      `,
    )
    .join("");
}

function exerciseCard(exercise, index) {
  const track = trackFor(exercise.track_id);
  const accent = track?.accent || "mint";
  const completed = state.completed.has(exercise.id);
  return `
    <a class="exercise-card" href="${exerciseUrl(exercise.id)}">
      <span class="card-topline">
        <span class="exercise-number">${String(index + 1).padStart(2, "0")}</span>
        <span class="exercise-kind-icon ${accent}">${typeIcon(exercise.kind)}</span>
      </span>
      <h2>${escapeHtml(exercise.title)}</h2>
      <p>${escapeHtml(exercise.description)}</p>
      <span class="card-meta">
        <span>${exercise.duration_minutes} daqiqa</span>
        <span class="card-action">${completed ? "Bajarildi" : "Ochish"} ${icons.arrow}</span>
      </span>
    </a>
  `;
}

function feedbackMarkup(exerciseId) {
  const feedback = state.feedback[exerciseId];
  if (!feedback) return "";
  const style = feedback.correct ? "correct" : feedback.type === "error" ? "incorrect" : "";
  return `<p class="feedback ${style}" role="status">${escapeHtml(feedback.message)}</p>`;
}

function practiceBody(exercise) {
  const answer = escapeHtml(state.answers[exercise.id] || "");

  if (exercise.kind === "pronunciation") {
    const recording = state.recordingId === exercise.id;
    return `
      <p class="target-phrase" lang="ru">${escapeHtml(exercise.target_text)}</p>
      <div class="exercise-actions">
        <button class="button button-secondary" data-action="record" data-exercise="${exercise.id}" type="button">
          ${icons.microphone}
          ${recording ? "Tinglanmoqda" : "Ovozni yozish"}
        </button>
      </div>
      <div class="answer-line">
        <input class="answer-input" data-answer-input="${exercise.id}" type="text" lang="ru" value="${answer}" placeholder="Aytilgan matn shu yerda paydo bo'ladi" autocomplete="off" />
        <button class="button button-primary" data-action="submit-answer" data-exercise="${exercise.id}" type="button">Tekshirish</button>
      </div>
      ${feedbackMarkup(exercise.id)}
    `;
  }

  if (exercise.kind === "listening_number") {
    return `
      <div class="exercise-actions">
        <button class="button button-primary" data-action="speak" data-exercise="${exercise.id}" type="button">
          ${icons.sound}
          Tinglash
        </button>
      </div>
      <div class="answer-line">
        <input class="answer-input" data-answer-input="${exercise.id}" type="text" inputmode="numeric" value="${answer}" placeholder="Sonni kiriting" autocomplete="off" />
        <button class="button button-secondary" data-action="submit-answer" data-exercise="${exercise.id}" type="button">Tekshirish</button>
      </div>
      ${feedbackMarkup(exercise.id)}
    `;
  }

  const choices = exercise.choices
    .map(
      (choice) => `
        <button class="choice-button ${state.answers[exercise.id] === choice.value ? "active" : ""}" data-action="select-choice" data-exercise="${exercise.id}" data-value="${escapeHtml(choice.value)}" type="button">
          <span class="choice-value">${escapeHtml(choice.value)}</span>
          <span class="choice-label">${escapeHtml(choice.label)}</span>
        </button>
      `,
    )
    .join("");
  return `
    <pre class="code-block"><code>${escapeHtml(exercise.code)}</code></pre>
    <div class="choice-list">${choices}</div>
    <div class="exercise-actions">
      <button class="button button-primary" data-action="submit-answer" data-exercise="${exercise.id}" type="button">
        Javobni tekshirish ${icons.arrow}
      </button>
    </div>
    ${feedbackMarkup(exercise.id)}
  `;
}

function practicePanel(exercise, showOverview = true) {
  const remaining = state.remainingSeconds[exercise.id] ?? exercise.duration_minutes * 60;
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
        <div>
          <p class="aside-description">${escapeHtml(exercise.description)}</p>
          ${exercise.hint ? `<p class="hint"><strong>Diqqat nuqtasi</strong>${escapeHtml(exercise.hint)}</p>` : ""}
        </div>
        <button class="button button-secondary timer-start" data-action="start-timer" data-exercise="${exercise.id}" type="button">
          ${icons.play}
          Taymerni boshlash
        </button>
      </aside>
    </section>
  `;
}

function renderCatalog() {
  const exercises = filteredExercises();
  const title = state.activeTrack === "all" ? "Mashqlar" : trackFor(state.activeTrack)?.title || "Mashqlar";

  appRoot.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <nav class="top-trackbar" aria-label="Yo'nalishlar">${topTrackButtons()}</nav>
      </header>
      <main id="main-content">
        <section class="exercise-zone" aria-labelledby="exercise-list-title">
          <div class="section-heading">
            <h1 id="exercise-list-title">${escapeHtml(title)}</h1>
            <span class="exercise-count">${String(exercises.length).padStart(2, "0")} mashq</span>
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
  const remaining = state.remainingSeconds[exercise.id] ?? exercise.duration_minutes * 60;
  appRoot.innerHTML = `
    <div class="app-shell">
      <header class="topbar detail-topbar">
        <a class="back-link" href="/">${icons.back}<span>Barcha mashqlar</span></a>
        <span class="detail-track">${escapeHtml(track?.title || typeLabel(exercise.kind))}</span>
      </header>
      <main id="main-content">
        <section class="exercise-zone exercise-detail-zone" aria-labelledby="exercise-title">
          <p class="panel-kicker">${escapeHtml(typeLabel(exercise.kind))} / ${escapeHtml(exercise.level)}</p>
          <div class="detail-title-row">
            <h1 id="exercise-title">${escapeHtml(exercise.title)}</h1>
            <time class="timer" id="exercise-timer" datetime="PT${remaining}S">${formatTimer(remaining)}</time>
          </div>
          <p class="instruction detail-instruction">${escapeHtml(exercise.instruction)}</p>
          ${practicePanel(exercise, false)}
        </section>
      </main>
    </div>
  `;
}

function renderError(message) {
  appRoot.innerHTML = `<div class="app-shell"><main id="main-content"><div class="error-state">${escapeHtml(message)}</div></main></div>`;
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
  window.speechSynthesis.speak(utterance);
}

function recordPronunciation(exercise) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    state.feedback[exercise.id] = { type: "error", message: "Ovozli yozuv bu brauzerda yo'q. Matnni qo'lda kiriting." };
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
