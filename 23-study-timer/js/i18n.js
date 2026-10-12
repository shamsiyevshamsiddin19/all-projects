/**
 * Yengil i18n qatlami. Standart til — o'zbekcha.
 * HTML'da `data-i18n`, `data-i18n-title`, `data-i18n-aria`, `data-i18n-placeholder`
 * atributlari orqali bog'lanadi.
 */
import { LANGS } from './constants.js';

const DICT = {
  uz: {
    'app.title': 'Zenith Study Timer — minimalist taymer',
    'brand.title': 'ZENITH CHRONO',
    'brand.badge': 'STUDIO',
    'brand.settings': 'SOZLAMALAR',
    'brand.settingsBadge': 'CONFIG',

    'drawer.open': 'Sozlamalar panelini ochish',
    'drawer.label': 'Taymer sozlamalari',
    'drawer.close': 'Panelni yopish (Esc)',
    'drawer.pin': 'Panelni qadash (P)',
    'drawer.settings': 'Sozlamalar (S)',
    'drawer.backToTimer': 'Taymerga qaytish',

    'group.mode': 'ISH REJIMI',
    'group.duration': 'VAQTNI SOZLASH',
    'group.target': 'MAQSADLI SANA',
    'group.pomodoro': 'POMODORO BOSQICHI',
    'group.pomodoroConfig': 'POMODORO SOZLAMALARI',
    'group.stopwatch': 'SEKUNDOMER',
    'group.clock': 'SOAT',
    'group.title': "SARLAVHA / MAQSAD (IXTIYORIY)",
    'group.reminders': 'ESLATMALAR',
    'group.controls': 'BOSHQARUV',
    'group.stats': 'STATISTIKA',
    'group.data': "MA'LUMOTLAR",
    'group.theme': 'FON MAVZUSI',
    'group.font': 'SHRIFT USLUBI',
    'group.lang': 'TIL / LANGUAGE',
    'group.sound': 'OVOZ VA SIGNAL',
    'group.ambient': 'FOKUS AMBIENTI',
    'group.display': "KO'RINISHLARNI BOSHQARISH",

    'mode.target': 'Maqsadli sana',
    'mode.duration': 'Davomiylik',
    'mode.pomodoro': 'Pomodoro',
    'mode.stopwatch': 'Sekundomer',
    'mode.clock': 'Soat',

    'label.days': 'KUN',
    'label.hours': 'SOAT',
    'label.minutes': 'DAQIQA',
    'label.seconds': 'SONIYA',
    'label.centis': 'ULUSH',
    'label.date': 'SANA',

    'input.days': 'Kun',
    'input.hours': 'Soat',
    'input.minutes': 'Daqiqa',
    'input.seconds': 'Soniya',
    'input.titlePlaceholder': 'Masalan: IMTIHON, LOYIHA TAQDIMOTI...',
    'input.targetLabel': 'Sana va vaqtni tanlang',

    'preset.5m': '5 daqiqa',
    'preset.15m': '15 daqiqa',
    'preset.25m': '25 daqiqa',
    'preset.30m': '30 daqiqa',
    'preset.45m': '45 daqiqa (dars)',
    'preset.1h': '1 soat',
    'preset.2h': '2 soat',
    'preset.24h': '1 kun (24 soat)',
    'preset.tomorrow': 'Ertaga 00:00',
    'preset.weekend': 'Hafta oxiri',
    'preset.monthEnd': 'Oy oxiri',
    'preset.days7': '+7 kun',
    'preset.days30': '+30 kun',
    'preset.newYear': 'Yangi yil',

    'pomo.work': 'Dars / Fokus',
    'pomo.shortBreak': 'Qisqa tanaffus',
    'pomo.longBreak': 'Uzun tanaffus',
    'pomo.cycles': 'Bajarilgan dars seanslari',
    'pomo.resetCycles': 'Sikllarni nolga qaytarish',
    'pomo.workMin': 'Dars (daq)',
    'pomo.shortMin': 'Qisqa (daq)',
    'pomo.longMin': 'Uzun (daq)',
    'pomo.cycleCount': 'Uzun tanaffusgacha',
    'pomo.autoStart': 'Keyingi bosqichni avtomatik boshlash',

    'sw.lap': 'Bosqich (Lap)',
    'sw.clearLaps': 'Bosqichlarni tozalash',
    'sw.noLaps': "Bosqichlar yo'q",

    'reminder.interval': 'Oraliq eslatish',
    'reminder.off': "O'chirilgan",
    'reminder.everyN': 'Har {n} daqiqada',
    'reminder.preEnd': 'Tugashidan 1 daqiqa oldin eslatish',
    'reminder.intervalFired': "{n} daqiqa o'tdi — fokusni davom ettiring!",
    'reminder.preEndFired': 'Yakunlanishiga 1 daqiqa qoldi.',
    'reminder.missedFinish': "Siz yo'q bo'lgan vaqtda taymer tugagan.",

    'ctrl.start': 'Boshlash',
    'ctrl.pause': "To'xtatish",
    'ctrl.reset': 'Qaytarish (R)',
    'ctrl.fullscreen': "To'liq ekran",
    'ctrl.rotate': 'Taymerni burish (90°)',
    'ctrl.zen': 'Zen rejim',
    'ctrl.add1m': '+1 daq',
    'ctrl.add5m': '+5 daq',
    'ctrl.add15m': '+15 daq',
    'ctrl.add1h': '+1 soat',
    'ctrl.sub5m': '−5 daq',

    'status.ready': 'TAYYOR',
    'status.running': 'SANALMOQDA',
    'status.paused': 'PAUZA',
    'status.focus': 'FOKUS VAQTI',
    'status.finished': 'VAQT TUGADI',
    'status.pomoWork': 'DARS FOKUSI',
    'status.pomoBreak': 'TANAFFUS',
    'status.stopwatch': 'SEKUNDOMER',
    'status.clock': 'HAQIQIY VAQT',
    'status.target': 'MAQSADGACHA',
    'status.targetDone': 'MAQSAD VAQTI YETDI',

    'stats.totalFocus': 'Umumiy fokus',
    'stats.sessions': 'Seanslar',
    'stats.today': 'Bugun',
    'stats.clear': 'Statistikani tozalash',
    'stats.clearConfirm': "Butun statistika va tarix o'chiriladi. Davom etasizmi?",

    'data.export': 'JSON eksport',
    'data.import': 'JSON import',
    'data.importOk': "Ma'lumotlar JSON fayldan muvaffaqiyatli tiklandi.",
    'data.importFail': "JSON faylni o'qishda xatolik: {msg}",
    'data.importInvalid': "Fayl tuzilmasi mos emas (Zenith zaxira fayli kutilgan).",

    'sound.alarm': 'Tugash signali',
    'sound.test': 'Ovozni testlash',
    'sound.volume': 'Ovoz balandligi',
    'sound.zen_bowl': 'Zen Singing Bowl',
    'sound.soft_bell': "Mayin billur qo'ng'iroq",
    'sound.digital_chime': 'Digital Chime',
    'sound.crystal': 'Billur gong',
    'sound.mute': "Ovoz o'chirilgan",
    'ambient.label': 'Orqa fon tovushi',
    'ambient.none': "O'chiq",
    'ambient.rain': "Mayin yomg'ir",
    'ambient.binaural': 'Binaural (4 Hz farq)',
    'ambient.space': 'Kosmik drone',
    'ambient.note': "Binaural effekt faqat naushnikda seziladi. Ta'siri ilmiy isbotlanmagan — did bo'yicha tanlang.",

    'display.showDays': "Birinchi ustunni ko'rsatish (kunlar)",
    'display.autoRotate': "Vertikal telefonda avtomatik 90° ga burish",
    'display.wakeLock': "Ekran o'chib qolmasligi (WakeLock)",
    'display.notify': 'Tizim eslatmalari (Desktop Notification)',
    'display.edgeHover': "Chap chetga kursor tekkanda panelni ochish",

    'shortcuts.title': 'KLAVIATURA TEZKOR TUGMALARI',
    'shortcuts.space': 'Start / Pauza',
    'shortcuts.s': 'Sozlamalar',
    'shortcuts.f': "To'liq ekran",
    'shortcuts.p': 'Panelni qadash',
    'shortcuts.r': "Qayta o'rnatish",
    'shortcuts.l': 'Bosqich (lap)',
    'shortcuts.esc': 'Yopish',
    'hint.space': 'boshlash uchun',

    'a11y.digits': 'Taymerni boshlash yoki pauza qilish',
    'a11y.timeLeft': 'Qolgan vaqt: {time}',
    'a11y.elapsed': "O'tgan vaqt: {time}",

    'unit.hour': 'soat',
    'unit.min': 'daq',
    'notify.finishedTitle': 'Zenith Study Timer',
    'notify.durationDone': '{min} daqiqalik taymer yakunlandi',
    'notify.pomoWorkDone': 'Dars seansi tugadi (#{n}) — tanaffus vaqti',
    'notify.pomoBreakDone': 'Tanaffus tugadi — keyingi darsga tayyorlaning',
    'notify.targetDone': 'Maqsad vaqti yetdi',
    'session.default': 'Fokus seansi'
  },

  en: {
    'app.title': 'Zenith Study Timer — minimalist countdown',
    'brand.title': 'ZENITH CHRONO',
    'brand.badge': 'STUDIO',
    'brand.settings': 'SETTINGS',
    'brand.settingsBadge': 'CONFIG',

    'drawer.open': 'Open the settings panel',
    'drawer.label': 'Timer settings',
    'drawer.close': 'Close panel (Esc)',
    'drawer.pin': 'Pin panel (P)',
    'drawer.settings': 'Settings (S)',
    'drawer.backToTimer': 'Back to timer',

    'group.mode': 'MODE',
    'group.duration': 'SET DURATION',
    'group.target': 'TARGET DATE',
    'group.pomodoro': 'POMODORO PHASE',
    'group.pomodoroConfig': 'POMODORO SETTINGS',
    'group.stopwatch': 'STOPWATCH',
    'group.clock': 'CLOCK',
    'group.title': 'TITLE / GOAL (OPTIONAL)',
    'group.reminders': 'REMINDERS',
    'group.controls': 'CONTROLS',
    'group.stats': 'STATISTICS',
    'group.data': 'DATA',
    'group.theme': 'THEME',
    'group.font': 'TYPEFACE',
    'group.lang': 'LANGUAGE',
    'group.sound': 'SOUND & ALARM',
    'group.ambient': 'FOCUS AMBIENCE',
    'group.display': 'DISPLAY OPTIONS',

    'mode.target': 'Target date',
    'mode.duration': 'Duration',
    'mode.pomodoro': 'Pomodoro',
    'mode.stopwatch': 'Stopwatch',
    'mode.clock': 'Clock',

    'label.days': 'DAYS',
    'label.hours': 'HOURS',
    'label.minutes': 'MINUTES',
    'label.seconds': 'SECONDS',
    'label.centis': 'CENTIS',
    'label.date': 'DATE',

    'input.days': 'Days',
    'input.hours': 'Hours',
    'input.minutes': 'Minutes',
    'input.seconds': 'Seconds',
    'input.titlePlaceholder': 'e.g. FINAL EXAM, PROJECT LAUNCH...',
    'input.targetLabel': 'Pick a date and time',

    'preset.5m': '5 min',
    'preset.15m': '15 min',
    'preset.25m': '25 min',
    'preset.30m': '30 min',
    'preset.45m': '45 min (lesson)',
    'preset.1h': '1 hour',
    'preset.2h': '2 hours',
    'preset.24h': '1 day (24 h)',
    'preset.tomorrow': 'Tomorrow 00:00',
    'preset.weekend': 'Weekend',
    'preset.monthEnd': 'End of month',
    'preset.days7': '+7 days',
    'preset.days30': '+30 days',
    'preset.newYear': 'New Year',

    'pomo.work': 'Focus',
    'pomo.shortBreak': 'Short break',
    'pomo.longBreak': 'Long break',
    'pomo.cycles': 'Completed focus sessions',
    'pomo.resetCycles': 'Reset cycle counter',
    'pomo.workMin': 'Focus (min)',
    'pomo.shortMin': 'Short (min)',
    'pomo.longMin': 'Long (min)',
    'pomo.cycleCount': 'Until long break',
    'pomo.autoStart': 'Auto-start the next phase',

    'sw.lap': 'Lap',
    'sw.clearLaps': 'Clear laps',
    'sw.noLaps': 'No laps yet',

    'reminder.interval': 'Interval reminder',
    'reminder.off': 'Off',
    'reminder.everyN': 'Every {n} minutes',
    'reminder.preEnd': 'Warn 1 minute before the end',
    'reminder.intervalFired': '{n} minutes elapsed — keep going!',
    'reminder.preEndFired': '1 minute left.',
    'reminder.missedFinish': 'The timer finished while you were away.',

    'ctrl.start': 'Start',
    'ctrl.pause': 'Pause',
    'ctrl.reset': 'Reset (R)',
    'ctrl.fullscreen': 'Fullscreen',
    'ctrl.rotate': 'Rotate timer (90°)',
    'ctrl.zen': 'Zen mode',
    'ctrl.add1m': '+1 min',
    'ctrl.add5m': '+5 min',
    'ctrl.add15m': '+15 min',
    'ctrl.add1h': '+1 hour',
    'ctrl.sub5m': '−5 min',

    'status.ready': 'READY',
    'status.running': 'COUNTING',
    'status.paused': 'PAUSED',
    'status.focus': 'FOCUS TIME',
    'status.finished': 'TIME IS UP',
    'status.pomoWork': 'FOCUS',
    'status.pomoBreak': 'BREAK',
    'status.stopwatch': 'STOPWATCH',
    'status.clock': 'LIVE CLOCK',
    'status.target': 'UNTIL TARGET',
    'status.targetDone': 'TARGET REACHED',

    'stats.totalFocus': 'Total focus',
    'stats.sessions': 'Sessions',
    'stats.today': 'Today',
    'stats.clear': 'Clear statistics',
    'stats.clearConfirm': 'This erases all statistics and history. Continue?',

    'data.export': 'Export JSON',
    'data.import': 'Import JSON',
    'data.importOk': 'Data restored from the JSON file.',
    'data.importFail': 'Could not read the JSON file: {msg}',
    'data.importInvalid': 'File structure does not match a Zenith backup.',

    'sound.alarm': 'Alarm sound',
    'sound.test': 'Test sound',
    'sound.volume': 'Volume',
    'sound.zen_bowl': 'Zen singing bowl',
    'sound.soft_bell': 'Soft crystal bell',
    'sound.digital_chime': 'Digital chime',
    'sound.crystal': 'Crystal gong',
    'sound.mute': 'Muted',
    'ambient.label': 'Background sound',
    'ambient.none': 'Off',
    'ambient.rain': 'Gentle rain',
    'ambient.binaural': 'Binaural (4 Hz offset)',
    'ambient.space': 'Deep space drone',
    'ambient.note': 'Binaural beats are only audible with headphones. The effect is not scientifically established — pick what you enjoy.',

    'display.showDays': 'Show the first column (days)',
    'display.autoRotate': 'Auto-rotate 90° on portrait phones',
    'display.wakeLock': 'Keep the screen awake (WakeLock)',
    'display.notify': 'System notifications',
    'display.edgeHover': 'Open the panel on left-edge hover',

    'shortcuts.title': 'KEYBOARD SHORTCUTS',
    'shortcuts.space': 'Start / Pause',
    'shortcuts.s': 'Settings',
    'shortcuts.f': 'Fullscreen',
    'shortcuts.p': 'Pin panel',
    'shortcuts.r': 'Reset',
    'shortcuts.l': 'Lap',
    'shortcuts.esc': 'Close',
    'hint.space': 'to start',

    'a11y.digits': 'Start or pause the timer',
    'a11y.timeLeft': 'Time left: {time}',
    'a11y.elapsed': 'Elapsed: {time}',

    'unit.hour': 'h',
    'unit.min': 'min',
    'notify.finishedTitle': 'Zenith Study Timer',
    'notify.durationDone': '{min}-minute timer finished',
    'notify.pomoWorkDone': 'Focus session done (#{n}) — break time',
    'notify.pomoBreakDone': 'Break over — back to focus',
    'notify.targetDone': 'Target time reached',
    'session.default': 'Focus session'
  }
};

let current = 'uz';

export function setLang(lang) {
  current = LANGS.includes(lang) ? lang : 'uz';
  return current;
}

export function getLang() {
  return current;
}

/** Tarjima. {kalit} shaklidagi o'rin egalari `vars` bilan to'ldiriladi. */
export function t(key, vars = {}) {
  const table = DICT[current] || DICT.uz;
  let str = table[key];
  if (str === undefined) str = DICT.uz[key];
  if (str === undefined) return key;
  return str.replace(/\{(\w+)\}/g, (_, name) =>
    Object.prototype.hasOwnProperty.call(vars, name) ? String(vars[name]) : `{${name}}`);
}

/** Barcha kalitlar ro'yxati (testlar uchun) */
export function keysOf(lang) {
  return Object.keys(DICT[lang] || {});
}

/**
 * DOM'dagi barcha data-i18n atributlarini qayta chizadi.
 * @param {ParentNode} root
 */
export function applyTranslations(root = document) {
  root.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  root.querySelectorAll('[data-i18n-title]').forEach((el) => {
    el.setAttribute('title', t(el.dataset.i18nTitle));
  });
  root.querySelectorAll('[data-i18n-aria]').forEach((el) => {
    el.setAttribute('aria-label', t(el.dataset.i18nAria));
  });
  root.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    el.setAttribute('placeholder', t(el.dataset.i18nPlaceholder));
  });
  if (root === document) {
    document.documentElement.lang = current;
  }
}
