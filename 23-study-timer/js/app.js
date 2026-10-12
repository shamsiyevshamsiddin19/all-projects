/**
 * Zenith Chrono — kontroller.
 * Bu fayl faqat bog'laydi: TimerEngine (mantiq) + UI (ko'rinish) + Storage + Audio.
 */
import {
  MODES, POMODORO_PHASES, MS, MINUTE, TICK_INTERVAL_MS,
  EDGE_HOVER_PX, EDGE_CLOSE_MARGIN_PX, RESIZE_DEBOUNCE_MS, ORIENTATION_SETTLE_MS,
  DEFAULT_DURATION
} from './constants.js';
import { TimerEngine } from './engine/timer-engine.js';
import {
  Storage, recordSession, emptyStatistics, normalizeState, looksLikeBackup
} from './storage.js';
import { UI, queryElements, statusKeyFor } from './ui.js';
import { zenithAudio } from './audio.js';
import { setLang, t } from './i18n.js';
import { toLocalInputValue, formatDurationHuman } from './format.js';
import {
  toggleFullscreen, isFullscreen, onFullscreenChange, WakeLockManager,
  isMobileViewport, isPortrait, notifications, debounce, registerServiceWorker
} from './platform.js';

function boot() {
  const { els, missing } = queryElements(document);
  if (missing.length > 0) {
    // Jim ishlamay qolish o'rniga ochiq xato: yetishmagan elementlar ko'rinadi
    console.error('[Zenith] HTML elementlari yetishmaydi:', missing.join(', '));
  }

  const ui = new UI(els);
  const storage = new Storage();
  const wakeLock = new WakeLockManager();
  const engine = new TimerEngine();

  /** Faqat sozlamalar va statistika shu yerda — taymer holati engine'da */
  let state = storage.load();
  let rafId = null;
  let audioUnlocked = false;

  /* ------------------------------------------------------------- saqlash */

  function snapshot() {
    return {
      ...state,
      settings: { ...state.settings, pomodoro: { ...engine.pomodoroConfig } },
      timerState: engine.serialize()
    };
  }

  const persist = () => storage.save(snapshot());
  const persistNow = () => storage.saveNow(snapshot());

  /* ------------------------------------------------------- sozlamalarni qo'llash */

  function applySettingsToUI() {
    const s = state.settings;
    setLang(s.lang);
    ui.applyLanguage();
    ui.setTheme(s.theme);
    ui.setFont(s.font);

    els.langSelect.value = s.lang;
    els.volumeSlider.value = String(s.volume);
    els.volumePercent.textContent = `${s.volume}%`;
    els.alarmSoundSelect.value = s.alarmSound;
    els.ambientSoundSelect.value = s.ambientSound;
    els.intervalReminderSelect.value = String(s.intervalReminderMinutes);
    els.checkPreEndWarning.checked = s.preEndWarning;
    els.checkShowDays.checked = s.showDays;
    els.checkAutoRotatePortrait.checked = s.autoRotatePortrait;
    els.checkWakeLock.checked = s.wakeLockEnabled;
    els.checkBrowserNotify.checked = s.browserNotify;
    els.checkEdgeHover.checked = s.edgeHoverEnabled;
    els.eventTitleInput.value = s.eventTitle;

    zenithAudio.setVolume(s.volume);
    engine.reminders.intervalMinutes = s.intervalReminderMinutes;
    engine.reminders.preEndWarning = s.preEndWarning;
    wakeLock.enabled = s.wakeLockEnabled;

    ui.setEventTitle(s.eventTitle);
    ui.setRotated(s.isRotated90);
    ui.renderStats(state.statistics);
    ui.renderPomodoro(engine);
    ui.renderLaps(engine.stopwatch.laps);
    if (engine.targetAt) els.targetDateTimeInput.value = toLocalInputValue(new Date(engine.targetAt));
    ui.writeDurationInputs(engine.configuredDurationSec);
    ui.applyMode(engine.mode);
  }

  /* --------------------------------------------------------------- chizish */

  function renderNow() {
    const sample = engine.sample();
    ui.render(sample, {
      showDays: state.settings.showDays,
      showClockDate: els.checkClockShowDate.checked,
      now: new Date()
    });
    ui.setStatus(statusKeyFor(sample), sample.running);
    if (sample.mode === MODES.POMODORO) ui.renderPomodoro(engine);
  }

  /* ------------------------------------------------------------- hodisalar */

  function handleEvents(events) {
    for (const ev of events) {
      if (ev.type === 'interval') {
        notify(t('reminder.interval'), t('reminder.intervalFired', { n: ev.minutes }), { chime: true });
      } else if (ev.type === 'preEnd') {
        notify(t('reminder.preEnd'), t('reminder.preEndFired'), { chime: true });
      } else if (ev.type === 'finished') {
        onFinished(ev);
      }
    }
    if (events.length > 0) persist();
  }

  function onFinished(ev) {
    zenithAudio.playAlarm(state.settings.alarmSound);

    let body;
    if (ev.mode === MODES.POMODORO) {
      body = ev.phase === POMODORO_PHASES.WORK
        ? t('notify.pomoWorkDone', { n: ev.cycles })
        : t('notify.pomoBreakDone');
    } else if (ev.mode === MODES.TARGET) {
      body = t('notify.targetDone');
    } else {
      body = t('notify.durationDone', { duration: formatDurationHuman(ev.nominalMs, t) });
    }

    if (ev.focusMs > 0) {
      state.statistics = recordSession(state.statistics, {
        focusMs: ev.focusMs,
        type: ev.mode,
        title: state.settings.eventTitle || t('session.default'),
        when: new Date()
      });
      ui.renderStats(state.statistics);
    }

    notify(t('notify.finishedTitle'), body, { chime: false });
    persistNow();
  }

  /** Toast + (ruxsat bo'lsa) tizim bildirishnomasi + ovoz */
  function notify(title, body, { chime = false } = {}) {
    ui.showToast(body);
    if (chime) zenithAudio.playReminderChime();
    if (state.settings.browserNotify) notifications.show(title, body);
  }

  /* ---------------------------------------------------------------- yuritish */

  function tick() {
    handleEvents(engine.tick());
    renderNow();
  }

  function startLoops() {
    setInterval(tick, TICK_INTERVAL_MS);
    loopRaf();
  }

  /** Sekundomerning yuzinchi ulushlari uchun silliq chizish */
  function loopRaf() {
    if (rafId !== null) cancelAnimationFrame(rafId);
    const step = () => {
      if (engine.mode === MODES.STOPWATCH && engine.stopwatch.running) {
        const sample = engine.sample();
        ui.render(sample, { showDays: state.settings.showDays, now: new Date() });
      }
      rafId = requestAnimationFrame(step);
    };
    rafId = requestAnimationFrame(step);
  }

  /* ----------------------------------------------------------- boshqaruvlar */

  function togglePlayPause() {
    unlockAudio();
    if (engine.mode === MODES.CLOCK) return;
    if (engine.mode === MODES.DURATION && engine.duration.totalMs <= 0) {
      const fromInputs = ui.readDurationInputs();
      engine.setConfiguredDuration(fromInputs > 0 ? fromInputs : DEFAULT_DURATION);
      ui.writeDurationInputs(engine.configuredDurationSec);
    }
    engine.toggle();
    if (engine.isRunning) wakeLock.request();
    renderNow();
    persist();
  }

  function resetCurrent() {
    engine.reset();
    if (engine.mode === MODES.DURATION) ui.writeDurationInputs(engine.configuredDurationSec);
    if (engine.mode === MODES.TARGET) els.targetDateTimeInput.value = '';
    ui.renderLaps(engine.stopwatch.laps);
    renderNow();
    persist();
  }

  function switchMode(mode) {
    engine.setMode(mode);
    ui.applyMode(mode);
    if (mode === MODES.DURATION) ui.writeDurationInputs(engine.configuredDurationSec);
    renderNow();
    persist();
  }

  function applyTargetPreset(type) {
    const now = new Date();
    let target = new Date(now.getTime());
    switch (type) {
      case 'tomorrow':
        target.setDate(target.getDate() + 1);
        target.setHours(0, 0, 0, 0);
        break;
      case 'weekend': {
        const dist = (6 - target.getDay() + 7) % 7 || 7;
        target.setDate(target.getDate() + dist);
        target.setHours(0, 0, 0, 0);
        break;
      }
      case 'month_end':
        target = new Date(target.getFullYear(), target.getMonth() + 1, 0, 23, 59, 59);
        break;
      case 'days_7':
        target.setDate(target.getDate() + 7);
        break;
      case 'days_30':
        target.setDate(target.getDate() + 30);
        break;
      case 'new_year':
        target = new Date(now.getFullYear() + 1, 0, 1, 0, 0, 0);
        break;
      default:
        return;
    }
    engine.setTarget(target);
    els.targetDateTimeInput.value = toLocalInputValue(target);
    renderNow();
    persist();
  }

  function unlockAudio() {
    if (audioUnlocked) return;
    audioUnlocked = zenithAudio.unlock();
  }

  /* ------------------------------------------------------------ eksport/import */

  function exportJson() {
    const data = persistNow();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `study-timer-backup-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function importJson(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onerror = () => ui.showToast(t('data.importFail', { msg: 'read error' }));
    reader.onload = (e) => {
      try {
        const parsed = JSON.parse(String(e.target.result));
        if (!looksLikeBackup(parsed)) {
          ui.showToast(t('data.importInvalid'));
          return;
        }
        state = normalizeState(parsed);
        engine.restore(state.timerState);
        engine.setPomodoroConfig(state.settings.pomodoro);
        applySettingsToUI();
        renderNow();
        persistNow();
        ui.showToast(t('data.importOk'));
      } catch (err) {
        ui.showToast(t('data.importFail', { msg: err.message }));
      }
    };
    reader.readAsText(file);
  }

  /* ------------------------------------------------------------- orientatsiya */

  function syncOrientation() {
    if (isMobileViewport() && state.settings.autoRotatePortrait) {
      state.settings.isRotated90 = isPortrait();
    }
    ui.setRotated(state.settings.isRotated90);
  }

  /* ------------------------------------------------------------- listenerlar */

  function wireEvents() {
    // Panelni ochish/yopish
    document.addEventListener('mousemove', (e) => {
      ui.resetIdle();
      if (!state.settings.edgeHoverEnabled) return;
      if (e.clientX <= EDGE_HOVER_PX && !ui.drawerOpen) {
        ui.openDrawer();
        return;
      }
      if (!ui.isPinned && ui.drawerOpen) {
        const threshold = els.settingsDrawer.offsetWidth + EDGE_CLOSE_MARGIN_PX;
        const tag = document.activeElement?.tagName;
        if (e.clientX > threshold && tag !== 'SELECT' && tag !== 'INPUT') ui.closeDrawer();
      }
    });
    document.addEventListener('keydown', () => ui.resetIdle(), { capture: true });
    document.addEventListener('pointerdown', unlockAudio, { once: true });
    document.addEventListener('keydown', unlockAudio, { once: true });

    els.hoverZone.addEventListener('click', () => ui.openDrawer());
    els.hoverZone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        ui.openDrawer();
        ui.focusFirst(els.settingsDrawer);
      }
    });
    els.drawerBackdrop.addEventListener('click', () => ui.closeDrawer({ force: true }));
    els.closeDrawerBtn.addEventListener('click', () => {
      ui.setPinned(false);
      ui.closeDrawer({ force: true });
    });
    els.pinDrawerBtn.addEventListener('click', () => ui.setPinned(!ui.isPinned));
    els.openSettingsHeaderBtn.addEventListener('click', () => {
      if (ui.settingsViewOpen) ui.showTimerView();
      else ui.showSettingsView();
    });
    els.backToTimerBtn.addEventListener('click', () => ui.showTimerView());

    // Rejimlar
    els.modeTabs.forEach((tab) => {
      tab.addEventListener('click', () => switchMode(tab.dataset.mode));
    });

    // Asosiy boshqaruv
    els.toggleRunBtn.addEventListener('click', togglePlayPause);
    els.digitsContainer.addEventListener('click', togglePlayPause);
    els.digitsContainer.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        togglePlayPause();
      }
    });
    els.resetBtn.addEventListener('click', resetCurrent);

    els.adjustChips.forEach((btn) => {
      btn.addEventListener('click', () => {
        engine.adjust(Number(btn.dataset.add) * MS);
        if (engine.mode === MODES.DURATION) ui.writeDurationInputs(engine.configuredDurationSec);
        renderNow();
        persist();
      });
    });

    // Davomiylik
    const onDurationInput = () => {
      const total = ui.readDurationInputs();
      engine.setConfiguredDuration(total);
      renderNow();
      persist();
    };
    [els.inputDays, els.inputHours, els.inputMinutes, els.inputSeconds].forEach((input) => {
      input.addEventListener('input', onDurationInput);
      input.addEventListener('blur', onDurationInput);
    });
    els.durationPresets.forEach((btn) => {
      btn.addEventListener('click', () => {
        unlockAudio();
        engine.setConfiguredDuration(Number(btn.dataset.duration), { applyNow: true });
        ui.writeDurationInputs(engine.configuredDurationSec);
        engine.start();
        wakeLock.request();
        renderNow();
        persist();
      });
    });

    // Maqsadli sana
    els.targetDateTimeInput.addEventListener('change', () => {
      const picked = new Date(els.targetDateTimeInput.value);
      if (!Number.isNaN(picked.getTime())) {
        engine.setTarget(picked);
        renderNow();
        persist();
      }
    });
    els.targetPresets.forEach((btn) => {
      btn.addEventListener('click', () => applyTargetPreset(btn.dataset.target));
    });

    // Pomodoro
    els.phaseBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        engine.switchPomoPhase(btn.dataset.phase);
        ui.renderPomodoro(engine);
        renderNow();
        persist();
      });
    });
    els.resetCyclesBtn.addEventListener('click', () => {
      engine.resetPomoCycles();
      ui.renderPomodoro(engine);
      persist();
    });
    const onPomoConfig = () => {
      engine.setPomodoroConfig({
        work: Number(els.inputPomoWork.value) * MINUTE,
        shortBreak: Number(els.inputPomoShort.value) * MINUTE,
        longBreak: Number(els.inputPomoLong.value) * MINUTE,
        cyclesPerLongBreak: Number(els.inputPomoCycles.value),
        autoStartNext: els.checkPomoAutoStart.checked
      });
      state.settings.pomodoro = { ...engine.pomodoroConfig };
      ui.renderPomodoro(engine);
      renderNow();
      persist();
    };
    [els.inputPomoWork, els.inputPomoShort, els.inputPomoLong, els.inputPomoCycles]
      .forEach((input) => {
        input.addEventListener('change', onPomoConfig);
        input.addEventListener('blur', onPomoConfig);
      });
    els.checkPomoAutoStart.addEventListener('change', onPomoConfig);

    // Sekundomer
    els.lapBtn.addEventListener('click', () => {
      if (!engine.stopwatch.running) return;
      engine.addLap();
      ui.renderLaps(engine.stopwatch.laps);
      persist();
    });
    els.clearLapsBtn.addEventListener('click', () => {
      engine.clearLaps();
      ui.renderLaps(engine.stopwatch.laps);
      persist();
    });

    // Soat
    els.checkClockShowDate.addEventListener('change', renderNow);

    // Sarlavha
    els.eventTitleInput.addEventListener('input', () => {
      state.settings.eventTitle = els.eventTitleInput.value.trim().slice(0, 60);
      ui.setEventTitle(state.settings.eventTitle);
      persist();
    });

    // Eslatmalar
    els.intervalReminderSelect.addEventListener('change', () => {
      state.settings.intervalReminderMinutes = Number(els.intervalReminderSelect.value) || 0;
      engine.reminders.intervalMinutes = state.settings.intervalReminderMinutes;
      persist();
    });
    els.checkPreEndWarning.addEventListener('change', () => {
      state.settings.preEndWarning = els.checkPreEndWarning.checked;
      engine.reminders.preEndWarning = state.settings.preEndWarning;
      persist();
    });

    // Til / mavzu / shrift
    els.langSelect.addEventListener('change', () => {
      state.settings.lang = els.langSelect.value;
      setLang(state.settings.lang);
      ui.applyLanguage();
      applySettingsToUI();
      renderNow();
      persist();
    });
    els.themeSelect.addEventListener('change', () => {
      state.settings.theme = els.themeSelect.value;
      ui.setTheme(state.settings.theme);
      persist();
    });
    els.fontSelect.addEventListener('change', () => {
      state.settings.font = els.fontSelect.value;
      ui.setFont(state.settings.font);
      persist();
    });

    // Ovoz
    els.alarmSoundSelect.addEventListener('change', () => {
      state.settings.alarmSound = els.alarmSoundSelect.value;
      unlockAudio();
      zenithAudio.playAlarm(state.settings.alarmSound);
      persist();
    });
    els.ambientSoundSelect.addEventListener('change', () => {
      state.settings.ambientSound = els.ambientSoundSelect.value;
      unlockAudio();
      zenithAudio.setAmbient(state.settings.ambientSound);
      persist();
    });
    els.volumeSlider.addEventListener('input', () => {
      state.settings.volume = Number(els.volumeSlider.value);
      els.volumePercent.textContent = `${state.settings.volume}%`;
      zenithAudio.setVolume(state.settings.volume);
      persist();
    });
    els.testSoundBtn.addEventListener('click', () => {
      unlockAudio();
      zenithAudio.playAlarm(state.settings.alarmSound);
    });

    // Ko'rinish sozlamalari
    els.checkShowDays.addEventListener('change', () => {
      state.settings.showDays = els.checkShowDays.checked;
      renderNow();
      persist();
    });
    els.checkAutoRotatePortrait.addEventListener('change', () => {
      state.settings.autoRotatePortrait = els.checkAutoRotatePortrait.checked;
      syncOrientation();
      persist();
    });
    els.checkWakeLock.addEventListener('change', async () => {
      state.settings.wakeLockEnabled = els.checkWakeLock.checked;
      await wakeLock.setEnabled(state.settings.wakeLockEnabled);
      persist();
    });
    els.checkBrowserNotify.addEventListener('change', async () => {
      const wanted = els.checkBrowserNotify.checked;
      if (wanted) {
        // Ruxsat faqat shu yerda so'raladi — sahifaga kirgan zahoti emas
        const perm = await notifications.requestPermission();
        state.settings.browserNotify = perm === 'granted';
        els.checkBrowserNotify.checked = state.settings.browserNotify;
      } else {
        state.settings.browserNotify = false;
      }
      persist();
    });
    els.checkEdgeHover.addEventListener('change', () => {
      state.settings.edgeHoverEnabled = els.checkEdgeHover.checked;
      persist();
    });

    // Ekran
    els.fullscreenBtn.addEventListener('click', async () => {
      ui.closeDrawer({ force: true });
      const active = await toggleFullscreen();
      ui.setFullscreenActive(active);
    });
    els.rotateTimerBtn.addEventListener('click', () => {
      state.settings.isRotated90 = !state.settings.isRotated90;
      ui.setRotated(state.settings.isRotated90);
      persist();
    });
    els.zenModeBtn.addEventListener('click', () => {
      ui.setPinned(false);
      ui.closeDrawer({ force: true });
      ui.enterZen();
    });

    // Statistika va ma'lumotlar
    els.clearStatsBtn.addEventListener('click', () => {
      if (!window.confirm(t('stats.clearConfirm'))) return;
      state.statistics = emptyStatistics();
      ui.renderStats(state.statistics);
      persistNow();
    });
    els.exportJsonBtn.addEventListener('click', exportJson);
    els.importJsonBtn.addEventListener('click', () => els.jsonFileInput.click());
    els.jsonFileInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      importJson(file);
      els.jsonFileInput.value = '';
    });

    // Klaviatura
    document.addEventListener('keydown', (e) => {
      const tag = e.target.tagName;
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(tag)) {
        if (e.key === 'Escape') {
          e.target.blur();
          if (ui.settingsViewOpen) ui.showTimerView();
          else ui.closeDrawer({ force: true });
        }
        return;
      }
      if (e.key === 'Tab') {
        ui.trapTab(e);
        return;
      }
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      switch (e.code) {
        case 'Space':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'KeyS':
          e.preventDefault();
          if (ui.settingsViewOpen) ui.showTimerView();
          else ui.showSettingsView();
          break;
        case 'KeyF':
          e.preventDefault();
          toggleFullscreen().then((active) => ui.setFullscreenActive(active));
          break;
        case 'KeyP':
          e.preventDefault();
          ui.setPinned(!ui.isPinned);
          break;
        case 'KeyR':
          e.preventDefault();
          resetCurrent();
          break;
        case 'KeyL':
          if (engine.mode === MODES.STOPWATCH && engine.stopwatch.running) {
            e.preventDefault();
            engine.addLap();
            ui.renderLaps(engine.stopwatch.laps);
            persist();
          }
          break;
        case 'Escape':
          if (ui.settingsViewOpen) ui.showTimerView();
          else ui.closeDrawer({ force: true });
          break;
        default:
          break;
      }
    });

    // Oyna va ko'rinish holati
    const onResize = debounce(syncOrientation, RESIZE_DEBOUNCE_MS);
    window.addEventListener('resize', onResize);
    window.addEventListener('orientationchange', () => setTimeout(syncOrientation, ORIENTATION_SETTLE_MS));
    onFullscreenChange(() => {
      const active = isFullscreen();
      if (!active) document.body.classList.remove('mobile-pseudo-fullscreen');
      ui.setFullscreenActive(active);
    });

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState !== 'visible') return;
      // Qaytganda: audio uyqudan chiqadi, WakeLock qayta olinadi, ekran yangilanadi
      zenithAudio.resumeIfNeeded();
      wakeLock.reacquire();
      tick();
    });

    window.addEventListener('beforeunload', () => storage.flush(snapshot()));
    window.addEventListener('pagehide', () => storage.flush(snapshot()));
  }

  /* ------------------------------------------------------------------- init */

  function init() {
    engine.setPomodoroConfig(state.settings.pomodoro);
    const restored = engine.restore(state.timerState);

    // Hech narsa yurib turmagan bo'lsa — ekran noldan boshlanadi (asl xulq)
    if (!restored.restoredRunning) {
      if (engine.mode === MODES.DURATION && !engine.duration.running) {
        engine.duration.reset(engine.duration.totalMs);
      }
    }

    applySettingsToUI();
    wireEvents();
    syncOrientation();
    ui.resetIdle();
    renderNow();
    startLoops();

    if (state.settings.ambientSound !== 'none') {
      // Avtoijro siyosati: birinchi bosishda yoqiladi
      zenithAudio.pendingAmbient = state.settings.ambientSound;
    }
    if (restored.missedFinish) {
      ui.showToast(t('reminder.missedFinish'));
    }

    registerServiceWorker('sw.js');

    // Server omboridagi nusxa yangiroq bo'lsa — sozlamalar va statistikani olamiz
    storage.fetchRemote(state.savedAt).then((remote) => {
      if (!remote) return;
      state = { ...state, settings: remote.settings, statistics: remote.statistics };
      engine.setPomodoroConfig(remote.settings.pomodoro);
      applySettingsToUI();
      renderNow();
    });
  }

  init();

  // Testlar va nosozlikni aniqlash uchun
  window.zenith = { engine, ui, storage, state: () => state, missingElements: missing };
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot);
} else {
  boot();
}
