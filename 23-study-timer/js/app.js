/**
 * Zenith Chrono — Main Application Controller
 * Handles timer states, modes, UI animations, mouse edge-detection, and JSON data persistence
 */

(function () {
  'use strict';

  // State Management
  const state = {
    mode: 'duration', // 'duration' | 'pomodoro' | 'stopwatch' | 'clock'
    isRunning: false,
    timerId: null,
    isPinned: false,
    
    // Target Date Mode (deprecated)
    targetDateTime: null,
    eventTitle: '',

    // Duration Mode
    durationTotal: 0,
    durationRemaining: 0,

    // Pomodoro Mode
    pomoPhase: 'work', // 'work' (25m) | 'shortBreak' (5m) | 'longBreak' (15m)
    pomoDurations: { work: 1500, shortBreak: 300, longBreak: 900 },
    pomoRemaining: 1500,
    pomoCompletedCycles: 0,

    // Stopwatch Mode
    stopwatchElapsed: 0,

    // Statistics & History
    totalFocusMinutes: 0,
    completedSessionsCount: 0,
    history: [],

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

    // Status & Controls
    statusPulse: document.getElementById('statusPulse'),
    statusText: document.getElementById('statusText'),
    playPauseIcon: document.getElementById('playPauseIcon'),
    playPauseText: document.getElementById('playPauseText'),
    toggleRunBtn: document.getElementById('toggleRunBtn'),
    resetBtn: document.getElementById('resetBtn'),

    // Theme & Font Selects
    themeSelect: document.getElementById('themeSelect'),
    fontSelect: document.getElementById('fontSelect'),

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

    // Statistics Displays
    totalFocusTimeDisplay: document.getElementById('totalFocusTimeDisplay'),
    completedSessionsDisplay: document.getElementById('completedSessionsDisplay'),
    exportJsonBtn: document.getElementById('exportJsonBtn'),
    importJsonBtn: document.getElementById('importJsonBtn'),
    jsonFileInput: document.getElementById('jsonFileInput'),

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
    zenModeBtn: document.getElementById('zenModeBtn'),

    // Settings Modal Elements
    openSettingsHeaderBtn: document.getElementById('openSettingsHeaderBtn'),
    openSettingsDrawerBtn: document.getElementById('openSettingsDrawerBtn'),
    openSettingsFloatingBtn: document.getElementById('openSettingsFloatingBtn'),
    settingsModalOverlay: document.getElementById('settingsModalOverlay'),
    closeSettingsModalBtn: document.getElementById('closeSettingsModalBtn'),
    saveCloseSettingsBtn: document.getElementById('saveCloseSettingsBtn')
  };

  // Helper: Format with leading zeros
  const pad = (n) => String(Math.max(0, Math.floor(n))).padStart(2, '0');

  /* ==========================================================================
     INITIALIZATION & JSON LOCAL STORAGE PERSISTENCE
     ========================================================================== */

  function init() {
    loadSettings();
    setupEventListeners();
    
    // User requirement: "saytga kirganda hammasi 0 tursin" and primary mode is Duration
    state.mode = 'duration';
    state.isRunning = false;
    state.durationRemaining = 0;
    state.durationTotal = 0;
    updateDurationInputs(0);

    applyModeUI();
    renderDigits(0, 0, 0, 0);
    updateStatus('TAYYOR', false);
    updateDisplay();
    startTimerLoop();
    resetIdleTimer();
    requestScreenWakeLock();
  }

  function loadSettings() {
    try {
      const saved = localStorage.getItem('zenith_timer_data') || localStorage.getItem('zenith_timer_config');
      if (saved) {
        const data = JSON.parse(saved);

        // Settings
        if (data.settings) {
          if (data.settings.theme) setTheme(data.settings.theme);
          if (data.settings.font) setFont(data.settings.font);
          if (data.settings.volume !== undefined) setVolume(data.settings.volume);
          if (data.settings.alarmSound) {
            state.alarmSound = data.settings.alarmSound;
            els.alarmSoundSelect.value = state.alarmSound;
          }
          if (data.settings.showDays !== undefined) {
            state.showDays = data.settings.showDays;
            els.checkShowDays.checked = state.showDays;
          }
          if (data.settings.showProgress !== undefined) {
            state.showProgress = data.settings.showProgress;
            els.checkShowProgress.checked = state.showProgress;
          }
          if (data.settings.eventTitle) {
            state.eventTitle = data.settings.eventTitle;
            els.eventTitleInput.value = state.eventTitle;
          }
          if (data.settings.mode) {
            state.mode = data.settings.mode === 'target' ? 'duration' : data.settings.mode;
          }
        } else {
          // Legacy format fallback
          if (data.theme) setTheme(data.theme);
          if (data.font) setFont(data.font);
          if (data.volume !== undefined) setVolume(data.volume);
          if (data.alarmSound) {
            state.alarmSound = data.alarmSound;
            els.alarmSoundSelect.value = state.alarmSound;
          }
          if (data.eventTitle) {
            state.eventTitle = data.eventTitle;
            els.eventTitleInput.value = state.eventTitle;
          }
        }

        // Timer States
        if (data.timerState) {
          if (data.timerState.targetDateTime) {
            state.targetDateTime = new Date(data.timerState.targetDateTime);
          }
          if (data.timerState.durationTotal) {
            state.durationTotal = data.timerState.durationTotal;
            state.durationRemaining = data.timerState.durationRemaining || data.timerState.durationTotal;
            updateDurationInputs(state.durationTotal);
          }
          if (data.timerState.pomoCompletedCycles !== undefined) {
            state.pomoCompletedCycles = data.timerState.pomoCompletedCycles;
            els.pomoCycleCount.textContent = state.pomoCompletedCycles;
          }
        }

        // Statistics
        if (data.statistics) {
          state.totalFocusMinutes = data.statistics.totalFocusMinutes || 0;
          state.completedSessionsCount = data.statistics.completedSessionsCount || 0;
          state.history = data.statistics.history || [];
        }
      }
    } catch (err) {
      console.warn('Config load error:', err);
    }

    updateStatsDisplays();
  }

  function saveSettings() {
    try {
      const data = {
        version: "1.0",
        savedAt: new Date().toISOString(),
        settings: {
          mode: state.mode,
          theme: state.theme,
          font: state.font,
          volume: state.volume,
          alarmSound: state.alarmSound,
          ambientSound: state.ambientSound,
          showDays: state.showDays,
          showProgress: state.showProgress,
          wakeLockEnabled: state.wakeLockEnabled,
          eventTitle: state.eventTitle
        },
        timerState: {
          targetDateTime: state.targetDateTime ? state.targetDateTime.toISOString() : null,
          durationTotal: state.durationTotal,
          durationRemaining: state.durationRemaining,
          pomoPhase: state.pomoPhase,
          pomoCompletedCycles: state.pomoCompletedCycles
        },
        statistics: {
          totalFocusMinutes: state.totalFocusMinutes,
          completedSessionsCount: state.completedSessionsCount,
          history: state.history.slice(-100) // Keep last 100 history entries
        }
      };

      // Save directly as JSON string to browser localStorage
      localStorage.setItem('zenith_timer_data', JSON.stringify(data));
      // Legacy backup
      localStorage.setItem('zenith_timer_config', JSON.stringify(data.settings));

      // Optional backend API sync if running via app.py
      if (window.location.protocol.startsWith('http')) {
        fetch('/api/data', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        }).catch(() => {}); // silent fail if static web
      }
    } catch (err) {
      console.warn('Config save error:', err);
    }
  }

  function setVolume(val) {
    state.volume = parseInt(val, 10);
    els.volumeSlider.value = state.volume;
    els.volumePercent.textContent = `${state.volume}%`;
    if (window.zenithAudio) window.zenithAudio.setVolume(state.volume);
  }

  function updateStatsDisplays() {
    if (els.totalFocusTimeDisplay) {
      if (state.totalFocusMinutes >= 60) {
        const hrs = (state.totalFocusMinutes / 60).toFixed(1);
        els.totalFocusTimeDisplay.textContent = `${hrs} soat`;
      } else {
        els.totalFocusTimeDisplay.textContent = `${state.totalFocusMinutes} daq`;
      }
    }
    if (els.completedSessionsDisplay) {
      els.completedSessionsDisplay.textContent = state.completedSessionsCount;
    }
  }

  /* ==========================================================================
     JSON EXPORT & IMPORT
     ========================================================================== */

  function exportToJson() {
    saveSettings();
    const rawData = localStorage.getItem('zenith_timer_data') || '{}';
    const parsed = JSON.parse(rawData);

    const jsonString = JSON.stringify(parsed, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const dateStr = new Date().toISOString().slice(0, 10);
    const a = document.createElement('a');
    a.href = url;
    a.download = `study-timer-backup-${dateStr}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function importFromJson(file) {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedData = JSON.parse(e.target.result);
        if (typeof importedData !== 'object' || importedData === null) {
          throw new Error('Noto\'g\'ri JSON formati');
        }

        // Store to localStorage
        localStorage.setItem('zenith_timer_data', JSON.stringify(importedData));
        
        // Re-read settings
        loadSettings();
        applyModeUI();
        updateDisplay();

        alert('✅ Ma\'lumotlar va sozlamalar JSON fayldan muvaffaqiyatli tiklandi!');
      } catch (err) {
        alert('❌ JSON faylni o\'qishda xatolik yuz berdi: ' + err.message);
      }
    };
    reader.readAsText(file);
  }

  /* ==========================================================================
     SETTINGS MODAL CONTROLLER
     ========================================================================== */

  function openSettingsModal() {
    if (els.settingsModalOverlay) {
      els.settingsModalOverlay.classList.add('active');
      els.settingsModalOverlay.setAttribute('aria-hidden', 'false');
    }
  }

  function closeSettingsModal() {
    if (els.settingsModalOverlay) {
      els.settingsModalOverlay.classList.remove('active');
      els.settingsModalOverlay.setAttribute('aria-hidden', 'true');
    }
  }

  function toggleSettingsModal() {
    if (els.settingsModalOverlay && els.settingsModalOverlay.classList.contains('active')) {
      closeSettingsModal();
    } else {
      openSettingsModal();
    }
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
    if (!state.targetDateTime) {
      renderDigits(0, 0, 0, 0);
      return;
    }

    const now = new Date().getTime();
    const target = state.targetDateTime.getTime();
    const diff = Math.max(0, target - now);

    if (diff <= 0) {
      state.isRunning = false;
      onTimerFinished('target', 'Maqsad vaqti yakunlandi');
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
      const mins = Math.max(1, Math.round(state.durationTotal / 60));
      onTimerFinished('duration', `${mins} daqiqalik taymer yakunlandi`, mins);
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
      if (state.pomoPhase === 'work') {
        state.pomoCompletedCycles++;
        els.pomoCycleCount.textContent = state.pomoCompletedCycles;
        onTimerFinished('pomodoro', `25 daqiqa fokus seansi (#${state.pomoCompletedCycles})`, 25);

        if (state.pomoCompletedCycles % 4 === 0) {
          switchPomoPhase('longBreak');
        } else {
          switchPomoPhase('shortBreak');
        }
      } else {
        onTimerFinished('break', 'Tanaffus tugadi, keyingi darsga tayyorlaning', 0);
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
    if (els.statusText) els.statusText.textContent = text;
    if (els.statusPulse) els.statusPulse.classList.toggle('paused', !running);
    if (els.playPauseText) els.playPauseText.textContent = running ? 'To\'xtatish' : 'Boshlash';

    // Update play/pause vector icon
    if (els.playPauseIcon) {
      if (running) {
        els.playPauseIcon.innerHTML = `<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;
      } else {
        els.playPauseIcon.innerHTML = `<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4"/></svg>`;
      }
    }
  }

  function onTimerFinished(type, title, focusMins = 0) {
    if (window.zenithAudio) {
      window.zenithAudio.playAlarm(state.alarmSound);
    }

    // Record session statistics
    if (focusMins > 0) {
      state.totalFocusMinutes += focusMins;
      state.completedSessionsCount++;
      state.history.push({
        id: Date.now(),
        timestamp: new Date().toISOString(),
        type: type,
        title: title || state.eventTitle || 'Fokus seansi',
        durationMinutes: focusMins
      });
      updateStatsDisplays();
      saveSettings(); // Auto-save updated stats to JSON
    }

    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Zenith Study Timer', { 
        body: title || 'Belgilangan vaqt yakunlandi!' 
      });
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
      if (state.mode === 'duration' && state.durationRemaining <= 0 && !state.isRunning) {
        openDrawer();
        if (els.inputMinutes) els.inputMinutes.focus();
        return;
      }
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
          saveSettings();
        } else if (state.mode === 'pomodoro') {
          state.pomoRemaining = Math.max(0, state.pomoRemaining + addSecs);
          tickPomodoro();
          saveSettings();
        }
      });
    });

    // 4. Mode Tabs
    els.modeTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const mode = tab.dataset.mode;
        setMode(mode);
        saveSettings();
      });
    });

    // 5. Target Date Input (if present)
    if (els.targetDateTimeInput) {
      els.targetDateTimeInput.addEventListener('change', () => {
        const selected = new Date(els.targetDateTimeInput.value);
        if (!isNaN(selected.getTime())) {
          state.targetDateTime = selected;
          state.isRunning = true;
          tickTarget();
          saveSettings();
        }
      });
    }

    // Target Presets
    document.querySelectorAll('#panelTarget .preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        applyTargetPreset(btn.dataset.target);
        saveSettings();
      });
    });

    // 6. Duration Inputs
    [els.inputDays, els.inputHours, els.inputMinutes, els.inputSeconds].forEach(inp => {
      inp.addEventListener('input', () => {
        updateDurationFromInputs();
        saveSettings();
      });
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
        saveSettings();
      });
    });

    // 7. Pomodoro Phase Buttons
    els.pomPhaseBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        switchPomoPhase(btn.dataset.phase);
        saveSettings();
      });
    });

    // 8. Event Title Input
    els.eventTitleInput.addEventListener('input', () => {
      state.eventTitle = els.eventTitleInput.value.trim();
      updateTitleDisplay();
      saveSettings();
    });

    // 9. Themes Selection (Dropdown & Chips)
    if (els.themeSelect) {
      els.themeSelect.addEventListener('change', () => {
        setTheme(els.themeSelect.value);
        saveSettings();
      });
    }
    document.querySelectorAll('.theme-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        setTheme(chip.dataset.theme);
        saveSettings();
      });
    });

    // 10. Fonts Selection (Dropdown & Chips)
    if (els.fontSelect) {
      els.fontSelect.addEventListener('change', () => {
        setFont(els.fontSelect.value);
        saveSettings();
      });
    }
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
      saveSettings();
    });

    els.volumeSlider.addEventListener('input', () => {
      setVolume(els.volumeSlider.value);
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
      saveSettings();
    });

    els.checkWakeLock.addEventListener('change', () => {
      state.wakeLockEnabled = els.checkWakeLock.checked;
      if (state.wakeLockEnabled) requestScreenWakeLock();
      else releaseScreenWakeLock();
      saveSettings();
    });

    // 13. JSON Export & Import Buttons
    if (els.exportJsonBtn) {
      els.exportJsonBtn.addEventListener('click', exportToJson);
    }
    if (els.importJsonBtn && els.jsonFileInput) {
      els.importJsonBtn.addEventListener('click', () => {
        els.jsonFileInput.click();
      });
      els.jsonFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          importFromJson(e.target.files[0]);
        }
      });
    }

    // 14. Fullscreen & Zen Mode & Settings Triggers
    els.fullscreenBtn.addEventListener('click', toggleFullscreen);
    els.zenModeBtn.addEventListener('click', () => {
      closeDrawer();
      triggerIdleNow();
    });

    if (els.openSettingsHeaderBtn) els.openSettingsHeaderBtn.addEventListener('click', openSettingsModal);
    if (els.openSettingsDrawerBtn) els.openSettingsDrawerBtn.addEventListener('click', openSettingsModal);
    if (els.openSettingsFloatingBtn) els.openSettingsFloatingBtn.addEventListener('click', openSettingsModal);
    if (els.closeSettingsModalBtn) els.closeSettingsModalBtn.addEventListener('click', closeSettingsModal);
    if (els.saveCloseSettingsBtn) els.saveCloseSettingsBtn.addEventListener('click', closeSettingsModal);

    if (els.settingsModalOverlay) {
      els.settingsModalOverlay.addEventListener('click', (e) => {
        if (e.target === els.settingsModalOverlay) closeSettingsModal();
      });
    }

    // 15. Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(e.target.tagName)) {
        if (e.key === 'Escape') {
          if (els.settingsModalOverlay && els.settingsModalOverlay.classList.contains('active')) {
            closeSettingsModal();
          } else {
            els.drawer.blur();
          }
        }
        return;
      }

      switch (e.code) {
        case 'Space':
          e.preventDefault();
          if (state.mode === 'duration' && state.durationRemaining <= 0 && !state.isRunning) {
            openDrawer();
            if (els.inputMinutes) els.inputMinutes.focus();
            return;
          }
          state.isRunning = !state.isRunning;
          updateStatus(state.isRunning ? 'SANALMOQDA' : 'PAUZA', state.isRunning);
          break;
        case 'KeyS':
          e.preventDefault();
          toggleSettingsModal();
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
          if (els.settingsModalOverlay && els.settingsModalOverlay.classList.contains('active')) {
            closeSettingsModal();
          } else {
            closeDrawer();
          }
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
    state.mode = mode === 'target' ? 'duration' : mode;
    els.modeTabs.forEach(t => t.classList.toggle('active', t.dataset.mode === state.mode));

    // Hide all mode panels
    if (els.panelTarget) els.panelTarget.classList.remove('active');
    if (els.panelDuration) els.panelDuration.classList.remove('active');
    if (els.panelPomodoro) els.panelPomodoro.classList.remove('active');

    // Show appropriate panel
    if (state.mode === 'duration' && els.panelDuration) els.panelDuration.classList.add('active');
    else if (state.mode === 'pomodoro' && els.panelPomodoro) els.panelPomodoro.classList.add('active');

    // Quick adjust chips visibility
    if (els.quickAdjustRow) {
      els.quickAdjustRow.style.display = (state.mode === 'duration' || state.mode === 'pomodoro') ? 'flex' : 'none';
    }

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
        if (state.targetDateTime) {
          state.isRunning = true;
          tickTarget();
        } else {
          state.isRunning = false;
          renderDigits(0, 0, 0, 0);
          updateStatus('TAYYOR', false);
        }
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

    if (els.themeSelect) {
      els.themeSelect.value = theme;
    }

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

    if (els.fontSelect) {
      els.fontSelect.value = font;
    }

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
    updateStatsDisplays();
    els.colDays.classList.toggle('hidden-col', !state.showDays);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
