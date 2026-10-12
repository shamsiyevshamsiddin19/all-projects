/**
 * UI qatlami: DOM keshi, chizish (render), panel (drawer), toast, statistika.
 * Mantiq yo'q — faqat holatni ekranga aks ettiradi.
 */
import {
  MODES, POMODORO_PHASES, THEMES, FONTS, REMINDER_INTERVALS, ALARM_SOUNDS,
  AMBIENT_SOUNDS, IDLE_HIDE_MS, TOAST_VISIBLE_MS, TOAST_FADE_MS, MINUTE, MS,
  INPUT_LIMITS
} from './constants.js';
import {
  pad2, splitDuration, splitRemaining, splitSeconds, formatCompact, formatFocusMinutes, dayKey
} from './format.js';
import { t, applyTranslations } from './i18n.js';
import { prefersReducedMotion } from './platform.js';

/**
 * Ilova ishlashi uchun HTML'da bo'lishi SHART bo'lgan elementlar.
 * `queryElements` yetishmaganini qaytaradi — testlar shuni tekshiradi,
 * shu sabab "null element" muammosi qaytib kelmaydi.
 */
export const REQUIRED_IDS = Object.freeze([
  'appBody', 'hoverZone', 'hoverPeekBar', 'drawerBackdrop', 'settingsDrawer',
  'drawerBrandTitle', 'drawerBrandBadge', 'openSettingsHeaderBtn', 'pinDrawerBtn',
  'closeDrawerBtn', 'timerSubView', 'settingsSubView', 'backToTimerBtn',
  'tabTarget', 'tabDuration', 'tabPomodoro', 'tabStopwatch', 'tabClock',
  'panelTarget', 'panelDuration', 'panelPomodoro', 'panelStopwatch', 'panelClock',
  'targetDateTimeInput',
  'inputDays', 'inputHours', 'inputMinutes', 'inputSeconds',
  'inputPomoWork', 'inputPomoShort', 'inputPomoLong', 'inputPomoCycles',
  'checkPomoAutoStart', 'phaseMinWork', 'phaseMinShort', 'phaseMinLong',
  'pomoCycleCount', 'pomoCycleTarget', 'resetCyclesBtn',
  'lapBtn', 'clearLapsBtn', 'lapsList', 'checkClockShowDate',
  'eventTitleInput', 'eventTitleBanner', 'eventTitleDisplay',
  'intervalReminderSelect', 'checkPreEndWarning',
  'toggleRunBtn', 'playPauseIcon', 'playPauseText', 'resetBtn', 'quickAdjustRow',
  'fullscreenBtn', 'rotateTimerBtn', 'zenModeBtn',
  'totalFocusTimeDisplay', 'completedSessionsDisplay', 'todayFocusDisplay', 'clearStatsBtn',
  'exportJsonBtn', 'importJsonBtn', 'jsonFileInput',
  'langSelect', 'themeSelect', 'fontSelect',
  'alarmSoundSelect', 'volumeSlider', 'volumePercent', 'testSoundBtn',
  'ambientSoundSelect', 'ambientNote',
  'checkShowDays', 'checkAutoRotatePortrait', 'checkWakeLock', 'checkBrowserNotify',
  'checkEdgeHover',
  'mainViewport', 'reminderToast', 'reminderToastText',
  'digitsContainer', 'colDays', 'colHours', 'colMinutes', 'colSeconds',
  'daysValue', 'hoursValue', 'minutesValue', 'secondsValue',
  'labelDays', 'labelHours', 'labelMinutes', 'labelSeconds',
  'srAnnounce', 'statusBar', 'statusPulse', 'statusText', 'hintText'
]);

/**
 * Elementlarni bir marta topadi va yetishmaganini aytadi.
 * @param {Document} doc
 */
export function queryElements(doc = document) {
  const els = {};
  const missing = [];
  for (const id of REQUIRED_IDS) {
    const el = doc.getElementById(id);
    if (el) els[id] = el;
    else missing.push(id);
  }
  els.modeTabs = Array.from(doc.querySelectorAll('.mode-tab'));
  els.phaseBtns = Array.from(doc.querySelectorAll('.phase-btn'));
  els.durationPresets = Array.from(doc.querySelectorAll('#panelDuration .preset-btn'));
  els.targetPresets = Array.from(doc.querySelectorAll('#panelTarget .preset-btn'));
  els.adjustChips = Array.from(doc.querySelectorAll('#quickAdjustRow .chip-btn'));
  return { els, missing };
}

/** Rejim ↔ panel/tab moslashuvi */
const MODE_PANEL = {
  [MODES.TARGET]: 'panelTarget',
  [MODES.DURATION]: 'panelDuration',
  [MODES.POMODORO]: 'panelPomodoro',
  [MODES.STOPWATCH]: 'panelStopwatch',
  [MODES.CLOCK]: 'panelClock'
};

export class UI {
  constructor(els) {
    this.els = els;
    this.isPinned = false;
    this.idleTimer = null;
    this.toastTimer = null;
    this.lastAnnouncedMinute = null;
    this.lastRendered = { d: null, h: null, m: null, s: null };
    this.reducedMotion = prefersReducedMotion();
  }

  /* ------------------------------------------------------- select'larni to'ldirish */

  /** Tilga bog'liq option'lar JS'dan yasaladi — til almashganda qayta chiziladi */
  buildSelectOptions() {
    const { intervalReminderSelect, alarmSoundSelect, ambientSoundSelect } = this.els;

    const fill = (select, items) => {
      const prev = select.value;
      select.textContent = '';
      for (const { value, label } of items) {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = label;
        select.appendChild(opt);
      }
      if (prev && items.some((i) => String(i.value) === prev)) select.value = prev;
    };

    fill(intervalReminderSelect, REMINDER_INTERVALS.map((n) => ({
      value: String(n),
      label: n === 0 ? t('reminder.off') : t('reminder.everyN', { n })
    })));
    fill(alarmSoundSelect, ALARM_SOUNDS.map((v) => ({ value: v, label: t(`sound.${v}`) })));
    fill(ambientSoundSelect, AMBIENT_SOUNDS.map((v) => ({ value: v, label: t(`ambient.${v}`) })));
  }

  /** Tarjimalarni va til bilan o'zgaradigan hamma narsani qayta chizadi */
  applyLanguage() {
    applyTranslations(document);
    this.buildSelectOptions();
    document.title = t('app.title');
  }

  /* ------------------------------------------------------------ mavzu / shrift */

  setTheme(theme) {
    const { appBody, themeSelect } = this.els;
    THEMES.forEach((cls) => appBody.classList.remove(cls));
    appBody.classList.add(THEMES.includes(theme) ? theme : THEMES[0]);
    themeSelect.value = theme;
  }

  setFont(font) {
    const { appBody, fontSelect } = this.els;
    FONTS.forEach((cls) => appBody.classList.remove(cls));
    appBody.classList.add(FONTS.includes(font) ? font : FONTS[0]);
    fontSelect.value = font;
  }

  /* -------------------------------------------------------------------- panel */

  openDrawer() {
    this.els.settingsDrawer.classList.add('open');
    this.els.drawerBackdrop.hidden = false;
    this.els.appBody.classList.add('drawer-open');
    this.resetIdle();
  }

  closeDrawer({ force = false } = {}) {
    if (this.isPinned && !force) return;
    this.els.settingsDrawer.classList.remove('open');
    this.els.drawerBackdrop.hidden = true;
    this.els.appBody.classList.remove('drawer-open');
  }

  get drawerOpen() {
    return this.els.settingsDrawer.classList.contains('open');
  }

  setPinned(pinned) {
    this.isPinned = Boolean(pinned);
    this.els.pinDrawerBtn.classList.toggle('active', this.isPinned);
    this.els.pinDrawerBtn.setAttribute('aria-pressed', String(this.isPinned));
    if (this.isPinned) this.openDrawer();
  }

  showSettingsView() {
    const { timerSubView, settingsSubView, openSettingsHeaderBtn, drawerBrandTitle, drawerBrandBadge } = this.els;
    timerSubView.hidden = true;
    timerSubView.classList.remove('active');
    settingsSubView.hidden = false;
    settingsSubView.classList.add('active');
    openSettingsHeaderBtn.classList.add('active');
    openSettingsHeaderBtn.setAttribute('aria-pressed', 'true');
    drawerBrandTitle.textContent = t('brand.settings');
    drawerBrandBadge.textContent = t('brand.settingsBadge');
    this.openDrawer();
    this.focusFirst(settingsSubView);
  }

  showTimerView() {
    const { timerSubView, settingsSubView, openSettingsHeaderBtn, drawerBrandTitle, drawerBrandBadge } = this.els;
    settingsSubView.hidden = true;
    settingsSubView.classList.remove('active');
    timerSubView.hidden = false;
    timerSubView.classList.add('active');
    openSettingsHeaderBtn.classList.remove('active');
    openSettingsHeaderBtn.setAttribute('aria-pressed', 'false');
    drawerBrandTitle.textContent = t('brand.title');
    drawerBrandBadge.textContent = t('brand.badge');
  }

  get settingsViewOpen() {
    return !this.els.settingsSubView.hidden;
  }

  /** Panel ichida fokusni ushlab turish (Tab halqasi) */
  focusablesIn(container) {
    return Array.from(container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )).filter((el) => !el.hidden && !el.disabled && el.offsetParent !== null);
  }

  focusFirst(container) {
    const list = this.focusablesIn(container);
    if (list.length > 0) list[0].focus();
  }

  trapTab(event) {
    if (!this.drawerOpen) return;
    const container = this.els.settingsDrawer;
    if (!container.contains(event.target)) return;
    const list = this.focusablesIn(container);
    if (list.length === 0) return;
    const first = list[0];
    const last = list[list.length - 1];
    if (event.shiftKey && event.target === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && event.target === last) {
      event.preventDefault();
      first.focus();
    }
  }

  /* --------------------------------------------------------------- rejim UI */

  applyMode(mode) {
    const { modeTabs } = this.els;
    modeTabs.forEach((tab) => {
      const active = tab.dataset.mode === mode;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', String(active));
    });
    for (const [modeKey, panelId] of Object.entries(MODE_PANEL)) {
      const panel = this.els[panelId];
      if (!panel) continue;
      const active = modeKey === mode;
      panel.classList.toggle('active', active);
      panel.hidden = !active;
    }
    const adjustable = mode === MODES.DURATION || mode === MODES.POMODORO || mode === MODES.TARGET;
    this.els.quickAdjustRow.hidden = !adjustable;
    this.els.appBody.dataset.mode = mode;
  }

  /* ------------------------------------------------------------------ chizish */

  /**
   * Taymerni ekranga chizadi.
   * @param {object} sample  TimerEngine.sample() natijasi
   * @param {{showDays:boolean, showClockDate:boolean, now:Date}} opts
   */
  render(sample, opts = {}) {
    const showDays = opts.showDays !== false;
    const now = opts.now || new Date();
    let columns;

    if (sample.mode === MODES.CLOCK) {
      columns = [
        { label: t('label.date'), value: pad2(now.getDate()), hidden: opts.showClockDate === false },
        { label: t('label.hours'), value: pad2(now.getHours()) },
        { label: t('label.minutes'), value: pad2(now.getMinutes()) },
        { label: t('label.seconds'), value: pad2(now.getSeconds()) }
      ];
    } else if (sample.mode === MODES.STOPWATCH) {
      const p = splitDuration(sample.elapsedMs);
      columns = [
        { label: t('label.hours'), value: pad2(p.days * 24 + p.hours) },
        { label: t('label.minutes'), value: pad2(p.minutes) },
        { label: t('label.seconds'), value: pad2(p.seconds) },
        { label: t('label.centis'), value: pad2(p.centis) }
      ];
    } else {
      // Orqaga sanashda yuqoriga yaxlitlanadi: 25:00 darhol 24:59 ga tushib ketmaydi
      const p = splitRemaining(sample.remainingMs);
      columns = [
        { label: t('label.days'), value: pad2(p.days), hidden: !showDays },
        { label: t('label.hours'), value: pad2(p.hours) },
        { label: t('label.minutes'), value: pad2(p.minutes) },
        { label: t('label.seconds'), value: pad2(p.seconds) }
      ];
    }

    this._paintColumns(columns);
    this._updateDocumentTitle(sample, now);
    this._announce(sample);
  }

  _paintColumns(columns) {
    const slots = [
      { col: this.els.colDays, value: this.els.daysValue, label: this.els.labelDays },
      { col: this.els.colHours, value: this.els.hoursValue, label: this.els.labelHours },
      { col: this.els.colMinutes, value: this.els.minutesValue, label: this.els.labelMinutes },
      { col: this.els.colSeconds, value: this.els.secondsValue, label: this.els.labelSeconds }
    ];
    columns.forEach((data, idx) => {
      const slot = slots[idx];
      if (!slot) return;
      slot.col.classList.toggle('hidden-col', Boolean(data.hidden));
      if (slot.label.textContent !== data.label) slot.label.textContent = data.label;
      if (slot.value.textContent !== data.value) this._pulseDigit(slot.value, data.value);
    });
  }

  /** Raqam almashganda nozik urg'u — reduced-motion'da animatsiya yo'q */
  _pulseDigit(el, text) {
    el.textContent = text;
    if (this.reducedMotion) return;
    el.classList.remove('digit-pulse');
    // reflow: animatsiya qayta ishga tushsin
    void el.offsetWidth;
    el.classList.add('digit-pulse');
  }

  _updateDocumentTitle(sample, now) {
    if (sample.mode === MODES.CLOCK) {
      document.title = `${pad2(now.getHours())}:${pad2(now.getMinutes())} — Zenith`;
      return;
    }
    if (!sample.running && sample.remainingMs <= 0) {
      document.title = t('app.title');
      return;
    }
    const countdown = sample.mode !== MODES.STOPWATCH;
    const ms = countdown ? sample.remainingMs : sample.elapsedMs;
    document.title = `${sample.running ? '⏱' : '⏸'} ${formatCompact(ms, { ceil: countdown })} — Zenith`;
  }

  /** Ekran o'quvchiga har daqiqada bir marta e'lon qiladi (har soniyada emas) */
  _announce(sample) {
    if (sample.mode === MODES.CLOCK) return;
    const countdown = sample.mode !== MODES.STOPWATCH;
    const ms = countdown ? sample.remainingMs : sample.elapsedMs;
    const minute = Math.floor(ms / (MINUTE * MS));
    if (minute === this.lastAnnouncedMinute) return;
    this.lastAnnouncedMinute = minute;
    const key = countdown ? 'a11y.timeLeft' : 'a11y.elapsed';
    this.els.srAnnounce.textContent = t(key, { time: formatCompact(ms, { ceil: countdown }) });
  }

  /* -------------------------------------------------------------------- status */

  setStatus(key, running) {
    this.els.statusText.textContent = t(key);
    this.els.statusPulse.classList.toggle('paused', !running);
    this.els.playPauseText.textContent = running ? t('ctrl.pause') : t('ctrl.start');
    this.els.playPauseIcon.innerHTML = running
      ? '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
      : '<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"/></svg>';
    this.els.hintText.hidden = running;
  }

  /* --------------------------------------------------------------------- toast */

  showToast(text) {
    const { reminderToast, reminderToastText } = this.els;
    reminderToastText.textContent = text;
    reminderToast.hidden = false;
    void reminderToast.offsetWidth;
    reminderToast.classList.add('active');
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => {
      reminderToast.classList.remove('active');
      setTimeout(() => {
        if (!reminderToast.classList.contains('active')) reminderToast.hidden = true;
      }, TOAST_FADE_MS);
    }, TOAST_VISIBLE_MS);
  }

  /* ---------------------------------------------------------------- sarlavha */

  setEventTitle(title) {
    const { eventTitleBanner, eventTitleDisplay } = this.els;
    if (title) {
      eventTitleDisplay.textContent = title;
      eventTitleBanner.hidden = false;
    } else {
      eventTitleBanner.hidden = true;
    }
  }

  /* ------------------------------------------------------------- kiritishlar */

  /** Kiritilgan qiymatlarni chegaralarga siqadi va qaytaradi */
  readDurationInputs() {
    const read = (el, limits) => {
      const raw = Math.floor(Number(el.value));
      const value = Number.isFinite(raw) ? Math.min(limits.max, Math.max(limits.min, raw)) : limits.min;
      if (String(value) !== el.value) el.value = String(value);
      return value;
    };
    const d = read(this.els.inputDays, INPUT_LIMITS.days);
    const h = read(this.els.inputHours, INPUT_LIMITS.hours);
    const m = read(this.els.inputMinutes, INPUT_LIMITS.minutes);
    const s = read(this.els.inputSeconds, INPUT_LIMITS.seconds);
    return d * 86400 + h * 3600 + m * 60 + s;
  }

  writeDurationInputs(totalSec) {
    const { days, hours, minutes, seconds } = splitSeconds(totalSec);
    this.els.inputDays.value = String(days);
    this.els.inputHours.value = String(hours);
    this.els.inputMinutes.value = String(minutes);
    this.els.inputSeconds.value = String(seconds);
  }

  /* --------------------------------------------------------------- pomodoro */

  renderPomodoro(engine) {
    const cfg = engine.pomodoroConfig;
    this.els.phaseMinWork.textContent = String(Math.round(cfg.work / MINUTE));
    this.els.phaseMinShort.textContent = String(Math.round(cfg.shortBreak / MINUTE));
    this.els.phaseMinLong.textContent = String(Math.round(cfg.longBreak / MINUTE));
    this.els.pomoCycleCount.textContent = String(engine.pomoCycles);
    this.els.pomoCycleTarget.textContent = String(cfg.cyclesPerLongBreak);
    this.els.phaseBtns.forEach((btn) => {
      const active = btn.dataset.phase === engine.pomoPhase;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-pressed', String(active));
    });
    this.els.inputPomoWork.value = String(Math.round(cfg.work / MINUTE));
    this.els.inputPomoShort.value = String(Math.round(cfg.shortBreak / MINUTE));
    this.els.inputPomoLong.value = String(Math.round(cfg.longBreak / MINUTE));
    this.els.inputPomoCycles.value = String(cfg.cyclesPerLongBreak);
    this.els.checkPomoAutoStart.checked = Boolean(cfg.autoStartNext);
  }

  /* -------------------------------------------------------------- sekundomer */

  renderLaps(laps) {
    const list = this.els.lapsList;
    list.textContent = '';
    if (!laps || laps.length === 0) {
      const li = document.createElement('li');
      li.className = 'lap-row lap-empty';
      li.textContent = t('sw.noLaps');
      list.appendChild(li);
      return;
    }
    for (const lap of [...laps].reverse()) {
      const li = document.createElement('li');
      li.className = 'lap-row';
      const idx = document.createElement('span');
      idx.className = 'lap-index';
      idx.textContent = `#${lap.index}`;
      const split = document.createElement('span');
      split.className = 'lap-split';
      split.textContent = formatCompact(lap.splitMs);
      const total = document.createElement('span');
      total.className = 'lap-total';
      total.textContent = formatCompact(lap.totalMs);
      li.append(idx, split, total);
      list.appendChild(li);
    }
  }

  /* -------------------------------------------------------------- statistika */

  renderStats(statistics) {
    this.els.totalFocusTimeDisplay.textContent = formatFocusMinutes(statistics.totalFocusMinutes, t);
    this.els.completedSessionsDisplay.textContent = String(statistics.completedSessionsCount);
    const today = statistics.byDay[dayKey()] || 0;
    this.els.todayFocusDisplay.textContent = formatFocusMinutes(today, t);
  }

  /* ------------------------------------------------------------------- zen */

  resetIdle() {
    this.els.appBody.classList.remove('user-idle');
    if (this.idleTimer) clearTimeout(this.idleTimer);
    this.idleTimer = setTimeout(() => {
      if (!this.isPinned && !this.drawerOpen) this.els.appBody.classList.add('user-idle');
    }, IDLE_HIDE_MS);
  }

  enterZen() {
    this.els.appBody.classList.add('user-idle');
  }

  setRotated(rotated) {
    this.els.appBody.classList.toggle('is-rotated-90', Boolean(rotated));
    this.els.rotateTimerBtn.classList.toggle('active', Boolean(rotated));
    this.els.rotateTimerBtn.setAttribute('aria-pressed', String(Boolean(rotated)));
  }

  setFullscreenActive(active) {
    this.els.fullscreenBtn.classList.toggle('active', Boolean(active));
    this.els.fullscreenBtn.setAttribute('aria-pressed', String(Boolean(active)));
  }
}

/** Pomodoro bosqichiga mos status kaliti */
export function statusKeyFor(sample) {
  switch (sample.mode) {
    case MODES.CLOCK: return 'status.clock';
    case MODES.STOPWATCH: return sample.running ? 'status.stopwatch' : 'status.ready';
    case MODES.TARGET:
      if (sample.finished) return 'status.targetDone';
      return sample.running ? 'status.target' : 'status.ready';
    case MODES.POMODORO:
      if (!sample.running) return 'status.ready';
      return sample.phase === POMODORO_PHASES.WORK ? 'status.pomoWork' : 'status.pomoBreak';
    case MODES.DURATION:
    default:
      if (sample.running) return 'status.focus';
      if (sample.finished) return 'status.finished';
      return 'status.ready';
  }
}
