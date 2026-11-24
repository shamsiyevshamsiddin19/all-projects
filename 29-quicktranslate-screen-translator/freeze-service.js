/**
 * Ekranni qotirish va maydondan matn o'qish overlayi
 * (Facade — quyi xizmatlarni bitta qulay interfeys ostiga yashiradi).
 *
 * Ketma-ketlik:
 *   1. Stage tasviri teksturaga olinadi va ekran ustiga qo'yiladi — ekran "qotadi";
 *   2. O'ynayotgan media MPRIS orqali pauzaga tushadi;
 *   3. Foydalanuvchi sichqoncha bilan MAYDON belgilaydi;
 *   4. Faqat o'sha maydon PNG'ga kesilib Tesseract'ga beriladi;
 *   5. Matn topilsa "Nusxalash" va "Tarjima qil" tugmalari chiqadi;
 *   6. Esc — overlay yopiladi, media davom etadi, vaqtinchalik rasm o'chiriladi.
 *
 * Nega butun ekran emas, maydon: butun ekran o'qilganda sarlavha, aktyor
 * ismlari va boshqa interfeys matni natijaga aralashib ketardi, ustiga
 * 1920x1080 ni o'qish sekin edi.
 *
 * Tarjima xizmatiga bog'lanmaydi: tarjima `onTranslate` callback'i orqali
 * tashqaridan beriladi (Dependency Inversion) — shuning uchun bu modulni
 * tarjimadan mustaqil sinash va o'zgartirish mumkin.
 */

import Clutter from 'gi://Clutter';
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import St from 'gi://St';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

import {RegionSelector} from './region-selector.js';
import {MediaPauseService} from './media-service.js';
import {captureFrozenFrame, deleteFrame, recognizeWords} from './ocr-service.js';
import {GlowOverlay} from './glow-overlay.js';
import {joinWords} from './tsv-parser.js';

const PILL_STYLE =
    'background-color: rgba(0,0,0,0.80); color: #ffffff; ' +
    'border-radius: 999px; padding: 8px 18px; font-size: 13px;';

const BAR_STYLE =
    'background-color: rgba(28,28,30,0.95); border-radius: 10px; ' +
    'padding: 6px; spacing: 6px;';

const BUTTON_STYLE =
    'background-color: rgba(255,255,255,0.12); color: #ffffff; ' +
    'border-radius: 7px; padding: 7px 14px; font-size: 13px;';

/** Amal paneli belgilangan maydondan shu qadar px pastda turadi. */
const BAR_GAP = 10;

export class FreezeOverlay {
    /**
     * @param {(text: string) => void} onTranslate  "Tarjima qil" bosilganda chaqiriladi
     * @param {() => string} getLanguages           OCR tillarini qaytaradi, masalan 'rus+eng'
     * @param {() => boolean} getGlowEnabled        chetdagi gradient halqa yoqilganmi
     */
    constructor(onTranslate, getLanguages, getGlowEnabled) {
        this._onTranslate = onTranslate;
        this._getLanguages = getLanguages;
        this._getGlowEnabled = getGlowEnabled;
        this._media = new MediaPauseService();
        this._reset();
    }

    get isOpen() {
        return this._container !== null;
    }

    _reset() {
        this._container = null;
        this._grab = null;
        this._selector = null;
        this._pill = null;
        this._bar = null;
        this._framePath = null;
        this._cancellable = null;
        this._pillTimeoutId = 0;
        this._glow = null;
        this._content = null;
        this._scale = 1;
        this._recognizedText = '';
    }

    /**
     * Pill taymerini bekor qiladi. Overlay yopilganda bu shart: aks holda
     * eski taymer keyingi overlayning xabarini vaqtidan oldin yashiradi.
     */
    _cancelPillTimeout() {
        if (this._pillTimeoutId) {
            GLib.source_remove(this._pillTimeoutId);
            this._pillTimeoutId = 0;
        }
    }

    /** Overlayni ochadi. Allaqachon ochiq bo'lsa hech narsa qilmaydi. */
    open() {
        if (this.isOpen)
            return;

        const shooter = new Shell.Screenshot();
        shooter.screenshot_stage_to_content((obj, res) => {
            let content, scale;
            try {
                [content, scale] = shooter.screenshot_stage_to_content_finish(res);
            } catch (e) {
                Main.notify('Quick Translate', `Ekran tasviri olinmadi: ${e.message}`);
                return;
            }
            this._build(content, scale);
        });
    }

    /**
     * Overlayni yopadi va vaqtinchalik faylni o'chiradi.
     *
     * @param {object} [options]
     * @param {boolean} [options.keepMediaPaused]  media pauzada qoldirilsinmi.
     *   Tarjima kartasiga o'tilayotganda `true` beriladi: karta ko'rinib
     *   turganda video o'ynab ketmasligi kerak. Keyin `resumeMedia()`
     *   chaqirilishi shart, aks holda video pauzada qolib ketadi.
     */
    close({keepMediaPaused = false} = {}) {
        if (!this.isOpen)
            return;

        this._cancellable?.cancel();
        this._cancelPillTimeout();
        deleteFrame(this._framePath);

        if (this._grab) {
            Main.popModal(this._grab);
            this._grab = null;
        }

        try {
            global.display.set_cursor(Meta.Cursor.DEFAULT);
        } catch (e) {
            // Kursor shaklini qaytarish muhim emas.
        }

        this._glow?.destroy();
        this._container.destroy();
        this._reset();

        if (!keepMediaPaused)
            this._media.resume();
    }

    /**
     * Qotirish uchun to'xtatilgan mediani davom ettiradi.
     *
     * Overlay yana ochiq bo'lsa hech narsa qilmaydi: aks holda tarjima
     * kartasi yopilganda yangi qotirish ortida video o'ynab ketardi.
     * Yangi overlay o'z navbatida yopilganda mediani o'zi davom ettiradi.
     */
    resumeMedia() {
        if (this.isOpen)
            return;
        this._media.resume();
    }

    /** Kengaytma o'chganda: mediani qaytarmasdan hammasini tozalash. */
    destroy() {
        if (this.isOpen) {
            this._cancellable?.cancel();
            this._cancelPillTimeout();
            deleteFrame(this._framePath);
            if (this._grab)
                Main.popModal(this._grab);
            this._glow?.destroy();
            this._container.destroy();
            this._reset();
        }
        this._media.forget();
    }

    _build(content, scale) {
        const width = global.stage.width;
        const height = global.stage.height;
        this._content = content;
        this._scale = scale;

        this._container = new St.Widget({
            reactive: true,
            can_focus: true,
            x: 0,
            y: 0,
            width,
            height,
        });

        // Qotgan kadr — animatsiya va blur yo'q (iGPU VRAM tejaladi).
        const frozen = new St.Widget({x: 0, y: 0, width, height, reactive: false});
        frozen.set_content(content);
        this._container.add_child(frozen);

        this._selector = new RegionSelector(width, height);
        this._container.add_child(this._selector);
        this._selector.connect('region-selected', () => this._onRegionSelected());

        // Rejimga kirilgani ko'rinib turishi uchun chetdagi gradient halqa.
        if (this._getGlowEnabled()) {
            this._glow = new GlowOverlay(this._container, width, height);
            // Hali hech narsa o'qilmayapti — maydon kutilmoqda.
            this._glow.setState('ready');
        }

        Main.layoutManager.addTopChrome(this._container);

        this._grab = Main.pushModal(this._container, {
            actionMode: Shell.ActionMode.POPUP,
        });
        this._container.grab_key_focus();
        this._container.connect('key-press-event', this._onKeyPress.bind(this));
        this._container.connect('button-press-event', (actor, event) => {
            // O'ng tugma — chiqish uchun qulay yo'l.
            if (event.get_button() === Clutter.BUTTON_SECONDARY) {
                this.close();
                return Clutter.EVENT_STOP;
            }
            return Clutter.EVENT_PROPAGATE;
        });

        try {
            global.display.set_cursor(Meta.Cursor.CROSSHAIR);
        } catch (e) {
            // Kursor shakli muhim emas — tanlash shundoq ham ishlaydi.
        }

        this._media.pausePlaying();
        this._showPill('Matn turgan joyni sichqoncha bilan belgilang');
    }

    /** Maydon tanlandi — faqat o'sha bo'lakni o'qiymiz. */
    _onRegionSelected() {
        const region = this._selector?.lastRegion;
        if (!region)
            return;

        this._bar?.hide();
        this._recognizedText = '';
        this._selector.setEnabled(false);
        this._glow?.setState('reading');
        this._showPill('O‘qilmoqda…');
        this._runOcr(region);
    }

    _runOcr(region) {
        this._cancellable?.cancel();
        this._cancellable = new Gio.Cancellable();
        const cancellable = this._cancellable;

        captureFrozenFrame(this._content, this._scale, region, (path, captureError) => {
            if (cancellable.is_cancelled() || !this.isOpen)
                return;
            if (captureError) {
                this._failed(captureError);
                return;
            }

            this._framePath = path;
            recognizeWords(path, this._getLanguages(), (words, ocrError) => {
                deleteFrame(path);
                this._framePath = null;

                if (cancellable.is_cancelled() || !this.isOpen)
                    return;
                if (ocrError) {
                    this._failed(ocrError);
                    return;
                }

                const text = joinWords(words);
                if (!text) {
                    this._failed('Bu maydonda matn topilmadi — boshqa joyni belgilang.');
                    return;
                }

                this._recognizedText = text;
                this._selector.setEnabled(true);
                this._glow?.setState('ready');
                this._showPill(`${words.length} so‘z o‘qildi`);
                this._hidePillLater();
                this._showBar(region);
            }, cancellable);
        });
    }

    /** O'qish muvaffaqiyatsiz: sabab ko'rsatiladi, yangi tanlovga ruxsat beriladi. */
    _failed(message) {
        this._recognizedText = '';
        this._selector?.setEnabled(true);
        this._glow?.setState('error');
        this._showPill(message);
    }

    _showBar(region) {
        if (!this._bar) {
            this._bar = new St.BoxLayout({style: BAR_STYLE, vertical: false});

            const copyButton = new St.Button({
                label: 'Nusxalash',
                style: BUTTON_STYLE,
                can_focus: true,
            });
            copyButton.connect('clicked', () => {
                this._copyRecognized();
                this.close();
            });

            const translateButton = new St.Button({
                label: 'Tarjima qil',
                style: BUTTON_STYLE,
                can_focus: true,
            });
            translateButton.connect('clicked', () => {
                const text = this._recognizedText;
                if (!text) {
                    this.close();
                    return;
                }
                // Media pauzada qoladi — tarjima kartasi yopilganda
                // `resumeMedia()` orqali davom etadi.
                this.close({keepMediaPaused: true});
                this._onTranslate(text);
            });

            this._bar.add_child(copyButton);
            this._bar.add_child(translateButton);
            this._container.add_child(this._bar);
        }

        // Panel halqadan ustda turishi uchun qayta ko'tariladi.
        this._container.set_child_above_sibling(this._bar, null);
        this._bar.show();
        if (!region)
            return;

        // Panelni maydon ostiga, ekran chegarasidan chiqmaydigan qilib qo'yamiz.
        const [, barWidth] = this._bar.get_preferred_width(-1);
        const [, barHeight] = this._bar.get_preferred_height(-1);
        let x = region.x + region.width / 2 - barWidth / 2;
        let y = region.y + region.height + BAR_GAP;

        x = Math.max(BAR_GAP, Math.min(x, global.stage.width - barWidth - BAR_GAP));
        if (y + barHeight > global.stage.height - BAR_GAP)
            y = Math.max(BAR_GAP, region.y - barHeight - BAR_GAP);

        this._bar.set_position(Math.round(x), Math.round(y));
    }

    _copyRecognized() {
        if (this._recognizedText)
            St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, this._recognizedText);
    }

    _showPill(message) {
        if (!this._pill) {
            this._pill = new St.Label({style: PILL_STYLE});
            this._container.add_child(this._pill);
        }
        this._cancelPillTimeout();
        this._container.set_child_above_sibling(this._pill, null);
        this._pill.set_text(message);
        this._pill.show();

        const [, pillWidth] = this._pill.get_preferred_width(-1);
        this._pill.set_position(Math.round((global.stage.width - pillWidth) / 2), 60);
    }

    _hidePillLater() {
        this._cancelPillTimeout();
        this._pillTimeoutId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, () => {
            this._pillTimeoutId = 0;
            this._pill?.hide();
            return GLib.SOURCE_REMOVE;
        });
    }

    _onKeyPress(actor, event) {
        const symbol = event.get_key_symbol();
        const state = event.get_state();
        const ctrl = (state & Clutter.ModifierType.CONTROL_MASK) !== 0;

        if (symbol === Clutter.KEY_Escape) {
            this.close();
            return Clutter.EVENT_STOP;
        }
        if (ctrl && (symbol === Clutter.KEY_c || symbol === Clutter.KEY_C)) {
            this._copyRecognized();
            this.close();
            return Clutter.EVENT_STOP;
        }
        if (ctrl && (symbol === Clutter.KEY_a || symbol === Clutter.KEY_A)) {
            this._selector?.selectAll();
            return Clutter.EVENT_STOP;
        }
        return Clutter.EVENT_PROPAGATE;
    }
}
