const appRoot = document.querySelector("#app");
const storageKey = "train.shamsiyev.uz.completed.v1";

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
    '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M14 7l5 5-5 5"></path></svg>',
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
  if (state.activeTrack === "all") {
    return state.exercises;
  }
  return state.exercises.filter((exercise) => exercise.track_id === state.activeTrack);
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
    if (Array.isArray(saved)) {
      state.completed = new Set(saved);
    }
  } catch {
    state.completed = new Set();
  }
}

function saveCompleted() {
  localStorage.setItem(storageKey, JSON.stringify([...state.completed]));
}

function trackButtons() {
  const allButton = {
    id: "all",
    title: "Barcha mashqlar",
    description: "Barcha yo'nalishlar",
    accent: "",
  };
  return [allButton, ...state.tracks]
    .map(
      (track) => `
        <button class="track-button ${state.activeTrack === track.id ? "active" : ""}" data-action="select-track" data-track="${track.id}" type="button">
          <span class="track-marker ${track.accent || ""}"></span>
          <span>
            <span class="track-name">${escapeHtml(track.title)}</span>
            <span class="track-caption">${escapeHtml(track.description)}</span>
          </span>
        </button>
      `,
    )
    .join("");
}

function exerciseCard(exercise, index) {
  const track = trackFor(exercise.track_id);
  const accent = track?.accent || "mint";
  const isCompleted = state.completed.has(exercise.id);
  return `
    <button class="exercise-card ${exercise.id === state.activeId ? "active" : ""}" data-action="open-exercise" data-exercise="${exercise.id}" type="button">
      <span class="card-topline">
        <span class="exercise-number">${String(index + 1).padStart(2, "0")}</span>
        <span class="exercise-kind-icon ${accent}">${typeIcon(exercise.kind)}</span>
      </span>
      <h3>${escapeHtml(exercise.title)}</h3>
      <p>${escapeHtml(exercise.description)}</p>
      <span class="card-meta">
        <span>${exercise.duration_minutes} daqiqa</span>
        <span>${isCompleted ? '<span class="completed-mark">Bajarildi</span>' : escapeHtml(typeLabel(exercise.kind))}</span>
      </span>
    </button>
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

function practicePanel(exercise) {
  const remaining = state.remainingSeconds[exercise.id] ?? exercise.duration_minutes * 60;
  return `
    <section class="practice-panel" id="practice-panel" aria-labelledby="practice-title">
      <div class="practice-content">
        <p class="panel-kicker">${escapeHtml(typeLabel(exercise.kind))} / ${escapeHtml(exercise.level)}</p>
        <div class="practice-title-row">
          <h2 id="practice-title">${escapeHtml(exercise.title)}</h2>
          <time class="timer" id="exercise-timer" datetime="PT${remaining}S">${formatTimer(remaining)}</time>
        </div>
        <p class="instruction">${escapeHtml(exercise.instruction)}</p>
        <div class="practice-body">${practiceBody(exercise)}</div>
      </div>
      <aside class="practice-aside" aria-label="Mashq yo'riqnomasi">
        <div>
          <p class="aside-description">${escapeHtml(exercise.description)}</p>
          ${
            exercise.hint
              ? `<p class="hint"><strong>Diqqat nuqtasi</strong>${escapeHtml(exercise.hint)}</p>`
              : ""
          }
        </div>
        <button class="button button-secondary timer-start" data-action="start-timer" data-exercise="${exercise.id}" type="button">
          ${icons.play}
          Taymerni boshlash
        </button>
      </aside>
    </section>
  `;
}

function render() {
  const exercises = filteredExercises();
  const current = activeExercise();
  const title = state.activeTrack === "all" ? "Mashqlar" : trackFor(state.activeTrack)?.title || "Mashqlar";
  const completed = state.completed.size;
  const progress = state.exercises.length ? Math.round((completed / state.exercises.length) * 100) : 0;

  appRoot.innerHTML = `
    <div class="app-shell">
      <header class="topbar">
        <a class="wordmark" href="/" aria-label="Bosh sahifa">train<span class="wordmark-dot">.</span></a>
        <div class="topbar-status"><span class="status-pulse"></span>Mustaqil mashq</div>
      </header>
      <main id="main-content">
        <section class="hero" aria-labelledby="page-title">
          <div>
            <p class="eyebrow">Har kuni aniq mashq</p>
            <h1 id="page-title">Diqqatni mashqqa yo'naltiring.</h1>
            <p class="hero-copy">Til va backend ko'nikmalarini qisqa sikllarda mustahkamlang. Bir mashq, bitta maqsad, aniq natija.</p>
          </div>
          <div class="daily-card" aria-label="Bugungi bajarilish holati">
            <div>
              <p class="daily-card-kicker">Bugungi natija</p>
              <strong>${completed} ta mashq bajarildi</strong>
              <p>Natija shu brauzerda saqlanadi.</p>
            </div>
            <div class="progress-ring" style="--progress: ${progress}%"><span>${progress}%</span></div>
          </div>
        </section>
        <div class="workspace">
          <aside class="track-panel" aria-label="Yo'nalishlar">
            <p class="section-kicker">Yo'nalishlar</p>
            <nav class="track-list">${trackButtons()}</nav>
            <div class="track-divider"></div>
            <p class="method-note">Qisqa siklni tugating, keyin keyingi mashqqa o'ting. Tezlikdan oldin aniqlik muhim.</p>
          </aside>
          <section class="exercise-zone" aria-labelledby="exercise-list-title">
            <div class="section-heading">
              <div>
                <p class="section-kicker">Tanlang va boshlang</p>
                <h2 id="exercise-list-title">${escapeHtml(title)}</h2>
              </div>
              <span class="exercise-count">${String(exercises.length).padStart(2, "0")} mashq</span>
            </div>
            ${exercises.length ? `<div class="exercise-grid">${exercises.map(exerciseCard).join("")}</div>` : "<p class=\"empty-state\">Bu yo'nalishda hozircha mashq yo'q.</p>"}
            ${current ? practicePanel(current) : ""}
          </section>
        </div>
      </main>
    </div>
  `;
}

function updateTimer() {
  const exercise = activeExercise();
  const timer = document.querySelector("#exercise-timer");
  if (exercise && timer) {
    const seconds = state.remainingSeconds[exercise.id] ?? exercise.duration_minutes * 60;
    timer.textContent = formatTimer(seconds);
    timer.dateTime = `PT${seconds}S`;
  }
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
      render();
    }
  }, 1000);
}

function speak(exercise) {
  if (!("speechSynthesis" in window) || !exercise.audio_text) {
    state.feedback[exercise.id] = { type: "error", message: "Bu brauzerda ovozli tinglash mavjud emas." };
    render();
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
    state.feedback[exercise.id] = {
      type: "error",
      message: "Ovozli yozuv bu brauzerda yo'q. Matnni qo'lda kiriting.",
    };
    render();
    return;
  }

  const recognition = new Recognition();
  recognition.lang = "ru-RU";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  state.recordingId = exercise.id;
  render();

  recognition.onresult = (event) => {
    state.answers[exercise.id] = event.results[0][0].transcript;
    state.recordingId = null;
    render();
  };
  recognition.onerror = () => {
    state.recordingId = null;
    state.feedback[exercise.id] = { type: "error", message: "Ovoz aniqlanmadi. Yana urinib ko'ring yoki matnni kiriting." };
    render();
  };
  recognition.onend = () => {
    if (state.recordingId === exercise.id) {
      state.recordingId = null;
      render();
    }
  };
  recognition.start();
}

async function submitAnswer(exercise) {
  const answer = state.answers[exercise.id]?.trim();
  if (!answer) {
    state.feedback[exercise.id] = { type: "info", message: "Avval javobni kiriting yoki variantni tanlang." };
    render();
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
  render();
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
    const next = filteredExercises()[0];
    if (next) state.activeId = next.id;
    render();
    return;
  }

  const exercise = state.exercises.find((item) => item.id === button.dataset.exercise);
  if (!exercise) return;

  if (action === "open-exercise") {
    state.activeId = exercise.id;
    render();
    window.requestAnimationFrame(() => document.querySelector("#practice-panel")?.scrollIntoView({ behavior: "smooth", block: "start" }));
  }
  if (action === "select-choice") {
    state.answers[exercise.id] = button.dataset.value;
    render();
  }
  if (action === "submit-answer") submitAnswer(exercise);
  if (action === "start-timer") startTimer(exercise.id);
  if (action === "speak") speak(exercise);
  if (action === "record") recordPronunciation(exercise);
});

async function initialize() {
  try {
    const [tracksResponse, exercisesResponse] = await Promise.all([
      fetch("/api/tracks"),
      fetch("/api/exercises"),
    ]);
    if (!tracksResponse.ok || !exercisesResponse.ok) throw new Error("catalog unavailable");
    state.tracks = await tracksResponse.json();
    state.exercises = await exercisesResponse.json();
    state.activeId = state.exercises[0]?.id || null;
    loadCompleted();
    render();
  } catch {
    appRoot.innerHTML = "<div class=\"app-shell\"><div class=\"error-state\">Mashqlarni yuklab bo'lmadi. Sahifani yangilab ko'ring.</div></div>";
  }
}

initialize();
