/**
 * Zenith Chrono — Main Application Controller
 * Handles timer states, modes, UI animations, mouse edge-detection, and keyboard shortcuts
 */

(function () {
  'use strict';

  // State Management
  const state = {
    mode: 'target', // 'target' | 'duration' | 'pomodoro' | 'stopwatch' | 'clock'
    isRunning: false,
    timerId: null,
    isPinned: false,
    
    // Target Date Mode
    targetDateTime: null,
    eventTitle: '',

    // Duration Mode
    durationTotal: 1500, // 25 min default
    durationRemaining: 1500,

    // Pomodoro Mode
    pomoPhase: 'work', // 'work' (25m) | 'shortBreak' (5m) | 'longBreak' (15m)
    pomoDurations: { work: 1500, shortBreak: 300, longBreak: 900 },
    pomoRemaining: 1500,
    pomoCompletedCycles: 0,

    // Stopwatch Mode
    stopwatchElapsed: 0,

    // Settings & Appearance
    theme: 'theme-obsidian',
    font: 'font-urbanist',
    showDays: true,
    showProgress: true,
    wakeLockEnabled: true,
    alarmSound: 'zen_bowl',
    ambientSound: 'none',
    volume: 80,

    // Idle Detection
    idleTimer: null,
    wakeLockSentinel: null
  };

  // DOM Elements Cache
  const els = {
    body: document.getElementById('appBody'),
    hoverZone: document.getElementById('hoverZone'),
    hoverPeekBar: document.getElementById('hoverPeekBar'),
    drawer: document.getElementById('settingsDrawer'),
    pinDrawerBtn: document.getElementById('pinDrawerBtn'),
    closeDrawerBtn: document.getElementById('closeDrawerBtn'),
    
    // Digits
    daysValue: document.getElementById('daysValue'),
    hoursValue: document.getElementById('hoursValue'),
    minutesValue: document.getElementById('minutesValue'),
    secondsValue: document.getElementById('secondsValue'),
    colDays: document.getElementById('colDays'),
    
    // Progress & Title
    progressBarFill: document.getElementById('progressBarFill'),
    progressBarContainer: document.getElementById('progressBarContainer'),
    eventTitleBanner: document.getElementById('eventTitleBanner'),
    eventTitleDisplay: document.getElementById('eventTitleDisplay'),
    eventTitleInput: document.getElementById('eventTitleInput'),

    // Status
    statusPulse: document.getElementById('statusPulse'),
    statusText: document.getElementById('statusText'),
    playPauseIcon: document.getElementById('playPauseIcon'),
    playPauseText: document.getElementById('playPauseText'),
    toggleRunBtn: document.getElementById('toggleRunBtn'),
    resetBtn: document.getElementById('resetBtn'),

    // Mode Panels & Tabs
    modeTabs: document.querySelectorAll('.mode-tab'),
    panelTarget: document.getElementById('panelTarget'),
    panelDuration: document.getElementById('panelDuration'),
    panelPomodoro: document.getElementById('panelPomodoro'),
    targetDateTimeInput: document.getElementById('targetDateTimeInput'),

    // Duration Inputs
    inputDays: document.getElementById('inputDays'),
    inputHours: document.getElementById('inputHours'),
    inputMinutes: document.getElementById('inputMinutes'),
    inputSeconds: document.getElementById('inputSeconds'),
    quickAdjustRow: document.getElementById('quickAdjustRow'),

    // Pomodoro
    pomoCycleCount: document.getElementById('pomoCycleCount'),
    pomPhaseBtns: document.querySelectorAll('.phase-btn'),

    // Audio & Settings
    alarmSoundSelect: document.getElementById('alarmSoundSelect'),
    ambientSoundSelect: document.getElementById('ambientSoundSelect'),
    volumeSlider: document.getElementById('volumeSlider'),
    volumePercent: document.getElementById('volumePercent'),

    // Checks & Actions
    checkShowDays: document.getElementById('checkShowDays'),
    checkShowProgress: document.getElementById('checkShowProgress'),
    checkWakeLock: document.getElementById('checkWakeLock'),
    fullscreenBtn: document.getElementById('fullscreenBtn'),
    zenModeBtn: document.getElementById('zenModeBtn')
  };

  // Helper: Format with leading zeros
  const pad = (n) => String(Math.max(0, Math.floor(n))).padStart(2, '0');

  /* ==========================================================================
     INITIALIZATION & LOCAL STORAGE
     ========================================================================== */

  function init() {
    loadSettings();
    setupEventListeners();
    setupTargetDefault();
    applyModeUI();
    updateDisplay();
    startTimerLoop();
    resetIdleTimer();
    requestScreenWakeLock();
  }

  function setupTargetDefault() {
    // If no target date, default to demo photo look (+5 days 22 hours 5 mins 1 sec)
    if (!state.targetDateTime) {
      const now = new Date();
      const demoTarget = new Date(now.getTime() + (5 * 86400 + 22 * 3600 + 5 * 60 + 1) * 1000);
      state.targetDateTime = demoTarget;
      state.isRunning = true;
    }
    
    // Set input value in local ISO string format
    const tzOffset = (new Date()).getTimezoneOffset() * 60000;
    const localISOTime = (new Date(state.targetDateTime.getTime() - tzOffset)).toISOString().slice(0, 16);
    els.targetDateTimeInput.value = localISOTime;
  }

  function loadSettings() {
    try {
      const saved = localStorage.getItem('zenith_timer_config');
      if (saved) {
        const data = JSON.parse(saved);
        if (data.theme) setTheme(data.theme);
        if (data.font) setFont(data.font);
        if (data.volume !== undefined) {
          state.volume = data.volume;
          els.volumeSlider.value = state.volume;
          els.volumePercent.textContent = `${state.volume}%`;
          if (window.zenithAudio) window.zenithAudio.setVolume(state.volume);
        }
        if (data.alarmSound) {
          state.alarmSound = data.alarmSound;
          els.alarmSoundSelect.value = state.alarmSound;
        }
        if (data.showDays !== undefined) {
          state.showDays = data.showDays;
          els.checkShowDays.checked = state.showDays;
        }
        if (data.eventTitle) {
          state.eventTitle = data.eventTitle;
          els.eventTitleInput.value = state.eventTitle;
          updateTitleDisplay();
        }
      }
    } catch (_) {}
  }

  function saveSettings() {
    try {
      const data = {
        theme: state.theme,
        font: state.font,
        volume: state.volume,
        alarmSound: state.alarmSound,
        showDays: state.showDays,
        eventTitle: state.eventTitle
      };
      localStorage.setItem('zenith_timer_config', JSON.stringify(data));
    } catch (_) {}
  }

  /* ==========================================================================
     EDGE HOVER & DRAWER CONTROL
     ========================================================================== */

  function openDrawer() {
    els.drawer.classList.add('open');
  }

  function closeDrawer() {
    if (!state.isPinned) {
      els.drawer.classList.remove('open');
    }
  }

  function togglePin() {
    state.isPinned = !state.isPinned;
    els.pinDrawerBtn.classList.toggle('active', state.isPinned);
    if (state.isPinned) {
      openDrawer();
    }
  }

  /* ==========================================================================
     TIMER ENGINE & CORE LOGIC
     ========================================================================== */

  function startTimerLoop() {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = setInterval(tick, 1000);
  }

  function tick() {
    if (!state.isRunning && state.mode !== 'clock') return;

    switch (state.mode) {
      case 'target':
        tickTarget();
        break;
      case 'duration':
        tickDuration();
        break;
      case 'pomodoro':
        tickPomodoro();
        break;
      case 'stopwatch':
        tickStopwatch();
        break;
      case 'clock':
        tickClock();
        break;
    }
  }

  function tickTarget() {
    const now = new Date().getTime();
    const target = state.targetDateTime.getTime();
    const diff = Math.max(0, target - now);

    if (diff <= 0) {
      state.isRunning = false;
      onTimerFinished();
      renderDigits(0, 0, 0, 0);
      updateStatus('YAKUNLANDI', false);
      return;
    }

    const totalSecs = Math.floor(diff / 1000);
    const days = Math.floor(totalSecs / 86400);
    const hours = Math.floor((totalSecs % 86400) / 3600);
    const minutes = Math.floor((totalSecs % 3600) / 60);
    const seconds = totalSecs % 60;

    renderDigits(days, hours, minutes, seconds);
    updateStatus('SANALMOQDA', true);
  }

  function tickDuration() {
    if (state.durationRemaining > 0) {
      state.durationRemaining--;
      renderSecondsAsDigits(state.durationRemaining);
      updateProgressBar(state.durationRemaining, state.durationTotal);
      updateStatus('FOKUS VAQTI', true);
    } else {
      state.isRunning = false;
      onTimerFinished();
      renderDigits(0, 0, 0, 0);
      updateStatus('VAQT TUGADI', false);
    }
  }

  function tickPomodoro() {
    if (state.pomoRemaining > 0) {
      state.pomoRemaining--;
      renderSecondsAsDigits(state.pomoRemaining);
      const total = state.pomoDurations[state.pomoPhase];
      updateProgressBar(state.pomoRemaining, total);
      updateStatus(state.pomoPhase === 'work' ? 'DARS FOKUSI' : 'TANAFFUS', true);
    } else {
      onTimerFinished();
      if (state.pomoPhase === 'work') {
        state.pomoCompletedCycles++;
        els.pomoCycleCount.textContent = state.pomoCompletedCycles;
        if (state.pomoCompletedCycles % 4 === 0) {
          switchPomoPhase('longBreak');
        } else {
          switchPomoPhase('shortBreak');
        }
      } else {
        switchPomoPhase('work');
      }
    }
  }

  function tickStopwatch() {
    state.stopwatchElapsed++;
    renderSecondsAsDigits(state.stopwatchElapsed);
    updateStatus('SEKUNDOMER', true);
  }

  function tickClock() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const seconds = now.getSeconds();
    const dayOfMonth = now.getDate();

    renderDigits(dayOfMonth, hours, minutes, seconds);
    updateStatus('HAQIQIY VAQT', true);
  }

  function renderSecondsAsDigits(totalSecs) {
    const days = Math.floor(totalSecs / 86400);
    const hours = Math.floor((totalSecs % 86400) / 3600);
    const minutes = Math.floor((totalSecs % 3600) / 60);
    const seconds = totalSecs % 60;
    renderDigits(days, hours, minutes, seconds);
  }

  function renderDigits(d, h, m, s) {
    const dStr = pad(d);
    const hStr = pad(h);
    const mStr = pad(m);
    const sStr = pad(s);

    if (els.daysValue.textContent !== dStr) pulseDigit(els.daysValue, dStr);
    if (els.hoursValue.textContent !== hStr) pulseDigit(els.hoursValue, hStr);
    if (els.minutesValue.textContent !== mStr) pulseDigit(els.minutesValue, mStr);
    if (els.secondsValue.textContent !== sStr) pulseDigit(els.secondsValue, sStr);
  }

  function pulseDigit(el, newText) {
    el.textContent = newText;
    el.classList.add('tick-pulse');
    setTimeout(() => el.classList.remove('tick-pulse'), 150);
  }

  function updateProgressBar(current, total) {
    if (!state.showProgress || total <= 0) {
      els.progressBarFill.style.width = '100%';
      return;
    }
    const percent = Math.max(0, Math.min(100, (current / total) * 100));
    els.progressBarFill.style.width = `${percent}%`;
  }

  function updateStatus(text, running) {
    els.statusText.textContent = text;
    els.statusPulse.classList.toggle('paused', !running);
    els.playPauseText.textContent = running ? 'To\'xtatish' : 'Boshlash';

    // Update play/pause vector icon
    if (running) {
      els.playPauseIcon.innerHTML = `<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
    } else {
      els.playPauseIcon.innerHTML = `<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4"/></svg>`;
    }
  }

  function onTimerFinished() {
    if (window.zenithAudio) {
      window.zenithAudio.playAlarm(state.alarmSound);
    }
    // Browser notification if permitted
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Zenith Timer', { body: 'Belgilangan vaqt yakunlandi!' });
    }
  }

  /* ==========================================================================
     UI CONTROLS & EVENT HANDLERS
     ========================================================================== */

  function setupEventListeners() {
    // 1. Mouse Edge Hover Detection
    document.addEventListener('mousemove', (e) => {
      resetIdleTimer();
      // If cursor is at extreme left (within 28px) and drawer is closed, open it
      if (e.clientX <= 28 && !els.drawer.classList.contains('open')) {
        openDrawer();
      } 
      // If cursor moves well beyond the drawer width + margin, close it
      else if (!state.isPinned && els.drawer.classList.contains('open')) {
        const threshold = els.drawer.offsetWidth + 25;
        if (e.clientX > threshold) {
          closeDrawer();
        }
      }
    });

    els.hoverPeekBar.addEventListener('click', openDrawer);
    els.closeDrawerBtn.addEventListener('click', () => {
      state.isPinned = false;
      els.pinDrawerBtn.classList.remove('active');
      closeDrawer();
    });
    els.pinDrawerBtn.addEventListener('click', togglePin);

    // 2. Play / Pause & Reset
    els.toggleRunBtn.addEventListener('click', () => {
      state.isRunning = !state.isRunning;
      updateStatus(state.isRunning ? 'SANALMOQDA' : 'PAUZA', state.isRunning);
    });

    els.resetBtn.addEventListener('click', resetCurrentMode);

    // 3. Quick Adjust Duration Chips (+1m, +5m, etc.)
    els.quickAdjustRow.querySelectorAll('.chip-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const addSecs = parseInt(btn.dataset.add, 10);
        if (state.mode === 'duration') {
          state.durationRemaining = Math.max(0, state.durationRemaining + addSecs);
          state.durationTotal = Math.max(state.durationRemaining, state.durationTotal);
          tickDuration();
        } else if (state.mode === 'pomodoro') {
          state.pomoRemaining = Math.max(0, state.pomoRemaining + addSecs);
          tickPomodoro();
        }
      });
    });

    // 4. Mode Tabs
    els.modeTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const mode = tab.dataset.mode;
        setMode(mode);
      });
    });

    // 5. Target Date Input
    els.targetDateTimeInput.addEventListener('change', () => {
      const selected = new Date(els.targetDateTimeInput.value);
      if (!isNaN(selected.getTime())) {
        state.targetDateTime = selected;
        state.isRunning = true;
        tickTarget();
      }
    });

    // Target Presets
    document.querySelectorAll('#panelTarget .preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        applyTargetPreset(btn.dataset.target);
      });
    });

    // 6. Duration Inputs
    [els.inputDays, els.inputHours, els.inputMinutes, els.inputSeconds].forEach(inp => {
      inp.addEventListener('input', updateDurationFromInputs);
    });

    // Duration Presets
    document.querySelectorAll('#panelDuration .preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const secs = parseInt(btn.dataset.duration, 10);
        state.durationTotal = secs;
        state.durationRemaining = secs;
        state.isRunning = true;
        updateDurationInputs(secs);
        tickDuration();
      });
    });

    // 7. Pomodoro Phase Buttons
    els.pomPhaseBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        switchPomoPhase(btn.dataset.phase);
      });
    });

    // 8. Event Title Input
    els.eventTitleInput.addEventListener('input', () => {
      state.eventTitle = els.eventTitleInput.value.trim();
      updateTitleDisplay();
      saveSettings();
    });

    // 9. Themes Selection
    document.querySelectorAll('.theme-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        setTheme(chip.dataset.theme);
        saveSettings();
      });
    });

    // 10. Fonts Selection
    document.querySelectorAll('.font-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        setFont(chip.dataset.font);
        saveSettings();
      });
    });

    // 11. Audio Controls
    els.alarmSoundSelect.addEventListener('change', () => {
      state.alarmSound = els.alarmSoundSelect.value;
      if (window.zenithAudio) window.zenithAudio.playAlarm(state.alarmSound);
      saveSettings();
    });

    els.ambientSoundSelect.addEventListener('change', () => {
      state.ambientSound = els.ambientSoundSelect.value;
      if (window.zenithAudio) window.zenithAudio.setAmbient(state.ambientSound);
    });

    els.volumeSlider.addEventListener('input', () => {
      state.volume = parseInt(els.volumeSlider.value, 10);
      els.volumePercent.textContent = `${state.volume}%`;
      if (window.zenithAudio) window.zenithAudio.setVolume(state.volume);
      saveSettings();
    });

    // 12. Display Checkboxes
    els.checkShowDays.addEventListener('change', () => {
      state.showDays = els.checkShowDays.checked;
      els.colDays.classList.toggle('hidden-col', !state.showDays);
      saveSettings();
    });

    els.checkShowProgress.addEventListener('change', () => {
      state.showProgress = els.checkShowProgress.checked;
      els.progressBarContainer.style.display = state.showProgress ? 'block' : 'none';
    });

    els.checkWakeLock.addEventListener('change', () => {
      state.wakeLockEnabled = els.checkWakeLock.checked;
      if (state.wakeLockEnabled) requestScreenWakeLock();
      else releaseScreenWakeLock();
    });

    // 13. Fullscreen & Zen Mode
    els.fullscreenBtn.addEventListener('click', toggleFullscreen);
    els.zenModeBtn.addEventListener('click', () => {
      closeDrawer();
      triggerIdleNow();
    });

    // 14. Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      // Ignore if user is typing in input
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) {
        if (e.key === 'Escape') els.drawer.blur();
        return;
      }

      switch (e.code) {
        case 'Space':
          e.preventDefault();
          state.isRunning = !state.isRunning;
          updateStatus(state.isRunning ? 'SANALMOQDA' : 'PAUZA', state.isRunning);
          break;
        case 'KeyF':
          e.preventDefault();
          toggleFullscreen();
          break;
        case 'KeyP':
          e.preventDefault();
          togglePin();
          break;
        case 'KeyR':
          e.preventDefault();
          resetCurrentMode();
          break;
        case 'Escape':
          closeDrawer();
          break;
      }
    });

    // Request Notification permission on first user click
    document.addEventListener('click', () => {
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }, { once: true });
  }

  /* ==========================================================================
     MODE SWITCHING & PRESETS
     ========================================================================== */

  function setMode(mode) {
    state.mode = mode;
    els.modeTabs.forEach(t => t.classList.toggle('active', t.dataset.mode === mode));

    // Hide all mode panels
    els.panelTarget.classList.remove('active');
    els.panelDuration.classList.remove('active');
    els.panelPomodoro.classList.remove('active');

    // Show appropriate panel
    if (mode === 'target') els.panelTarget.classList.add('active');
    else if (mode === 'duration') els.panelDuration.classList.add('active');
    else if (mode === 'pomodoro') els.panelPomodoro.classList.add('active');

    // Quick adjust chips visibility
    els.quickAdjustRow.style.display = (mode === 'duration' || mode === 'pomodoro') ? 'flex' : 'none';

    // Reset and initialize mode state
    resetCurrentMode();
  }

  function applyModeUI() {
    setMode(state.mode);
  }

  function resetCurrentMode() {
    state.isRunning = false;
    els.progressBarFill.style.width = '100%';

    switch (state.mode) {
      case 'target':
        state.isRunning = true;
        tickTarget();
        break;
      case 'duration':
        state.durationRemaining = state.durationTotal;
        renderSecondsAsDigits(state.durationRemaining);
        updateStatus('TAYYOR', false);
        break;
      case 'pomodoro':
        state.pomoRemaining = state.pomoDurations[state.pomoPhase];
        renderSecondsAsDigits(state.pomoRemaining);
        updateStatus('POMODORO TAYYOR', false);
        break;
      case 'stopwatch':
        state.stopwatchElapsed = 0;
        renderDigits(0, 0, 0, 0);
        updateStatus('SEKUNDOMER TAYYOR', false);
        break;
      case 'clock':
        state.isRunning = true;
        tickClock();
        break;
    }
  }

  function applyTargetPreset(type) {
    const now = new Date();
    let target = new Date();

    switch (type) {
      case 'tomorrow':
        target.setDate(target.getDate() + 1);
        target.setHours(0, 0, 0, 0);
        break;
      case 'weekend':
        const day = target.getDay();
        const dist = (6 - day + 7) % 7 || 7;
        target.setDate(target.getDate() + dist);
        target.setHours(0, 0, 0, 0);
        break;
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
        target = new Date(2027, 0, 1, 0, 0, 0);
        break;
      case 'demo_photo':
        // Exactly matches user's photo: 5 days, 22 hours, 5 minutes, 1 second
        target = new Date(now.getTime() + (5 * 86400 + 22 * 3600 + 5 * 60 + 1) * 1000);
        break;
    }

    state.targetDateTime = target;
    const tzOffset = (new Date()).getTimezoneOffset() * 60000;
    els.targetDateTimeInput.value = (new Date(target.getTime() - tzOffset)).toISOString().slice(0, 16);
    state.isRunning = true;
    tickTarget();
  }

  function updateDurationFromInputs() {
    const d = parseInt(els.inputDays.value, 10) || 0;
    const h = parseInt(els.inputHours.value, 10) || 0;
    const m = parseInt(els.inputMinutes.value, 10) || 0;
    const s = parseInt(els.inputSeconds.value, 10) || 0;

    const total = d * 86400 + h * 3600 + m * 60 + s;
    state.durationTotal = total;
    state.durationRemaining = total;
    renderSecondsAsDigits(total);
  }

  function updateDurationInputs(secs) {
    const d = Math.floor(secs / 86400);
    const h = Math.floor((secs % 86400) / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;

    els.inputDays.value = d;
    els.inputHours.value = h;
    els.inputMinutes.value = m;
    els.inputSeconds.value = s;
  }

  function switchPomoPhase(phase) {
    state.pomoPhase = phase;
    state.pomoRemaining = state.pomoDurations[phase];
    els.pomPhaseBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.phase === phase));
    renderSecondsAsDigits(state.pomoRemaining);
    updateStatus(phase === 'work' ? 'DARS FOKUSI' : 'TANAFFUS', state.isRunning);
  }

  function updateTitleDisplay() {
    if (state.eventTitle) {
      els.eventTitleDisplay.textContent = state.eventTitle;
      els.eventTitleBanner.style.display = 'block';
    } else {
      els.eventTitleBanner.style.display = 'none';
    }
  }

  /* ==========================================================================
     THEMES & FONTS
     ========================================================================== */

  function setTheme(theme) {
    state.theme = theme;
    ['theme-obsidian', 'theme-midnight', 'theme-emerald', 'theme-amber', 'theme-violet', 'theme-aurora'].forEach(t => {
      els.body.classList.remove(t);
    });
    els.body.classList.add(theme);

    document.querySelectorAll('.theme-chip').forEach(c => {
      c.classList.toggle('active', c.dataset.theme === theme);
    });
  }

  function setFont(font) {
    state.font = font;
    ['font-urbanist', 'font-inter', 'font-montserrat', 'font-mono', 'font-serif'].forEach(f => {
      els.body.classList.remove(f);
    });
    els.body.classList.add(font);

    document.querySelectorAll('.font-chip').forEach(c => {
      c.classList.toggle('active', c.dataset.font === font);
    });
  }

  /* ==========================================================================
     FULLSCREEN & WAKELOCK & ZEN MODE
     ========================================================================== */

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) document.exitFullscreen();
    }
  }

  async function requestScreenWakeLock() {
    if ('wakeLock' in navigator && state.wakeLockEnabled) {
      try {
        state.wakeLockSentinel = await navigator.wakeLock.request('screen');
      } catch (_) {}
    }
  }

  function releaseScreenWakeLock() {
    if (state.wakeLockSentinel) {
      state.wakeLockSentinel.release().catch(() => {});
      state.wakeLockSentinel = null;
    }
  }

  function resetIdleTimer() {
    els.body.classList.remove('user-idle');
    if (state.idleTimer) clearTimeout(state.idleTimer);
    state.idleTimer = setTimeout(() => {
      // Only go idle if drawer is not pinned open
      if (!state.isPinned && !els.drawer.classList.contains('open')) {
        els.body.classList.add('user-idle');
      }
    }, 3500);
  }

  function triggerIdleNow() {
    els.body.classList.add('user-idle');
  }

  function updateDisplay() {
    updateTitleDisplay();
    els.colDays.classList.toggle('hidden-col', !state.showDays);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
