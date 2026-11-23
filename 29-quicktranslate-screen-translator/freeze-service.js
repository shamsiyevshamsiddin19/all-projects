/**
 * Ekranni qotirish va matn ajratish overlayi (Facade — quyi xizmatlarni
 * bitta qulay interfeys ostiga yashiradi).
 *
 * Ketma-ketlik:
 *   1. Stage tasviri teksturaga olinadi va ekran ustiga qo'yiladi — ekran "qotadi";
 *   2. O'ynayotgan media MPRIS orqali pauzaga tushadi;
 *   3. Shu qotgan kadr PNG'ga yozilib Tesseract'ga beriladi;
 *   4. So'z to'rtburchaklari ustiga Live Text belgilash qatlami qo'yiladi;
 *   5. Esc — overlay yopiladi, media davom etadi, vaqtinchalik rasm o'chiriladi.
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

import {TextSelectionLayer} from './text-layer.js';
import {MediaPauseService} from './media-service.js';
import {captureFrozenFrame, deleteFrame, recognizeWords} from './ocr-service.js';
import {GlowOverlay} from './glow-overlay.js';

const PILL_STYLE =
    'background-color: rgba(0,0,0,0.80); color: #ffffff; ' +
    'border-radius: 999px; padding: 8px 18px; font-size: 13px;';

const BAR_STYLE =
    'background-color: rgba(28,28,30,0.95); border-radius: 10px; ' +
    'padding: 6px; spacing: 6px;';

const BUTTON_STYLE =
    'background-color: rgba(255,255,255,0.12); color: #ffffff; ' +
    'border-radius: 7px; padding: 7px 14px; font-size: 13px;';

/** Amal paneli belgilangan matndan shu qadar px pastda turadi. */
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
        this._textLayer = null;
        this._pill = null;
        this._bar = null;
        this._framePath = null;
        this._cancellable = null;
        this._pillTimeoutId = 0;
        this._glow = null;
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

    /** Overlayni yopadi, mediani davom ettiradi, vaqtinchalik faylni o'chiradi. */
    close() {
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

        // Rejimga kirilgani ko'rinib turishi uchun chetdagi gradient halqa.
        if (this._getGlowEnabled())
            this._glow = new GlowOverlay(this._container, width, height);

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

        this._media.pausePlaying();
        this._showPill("Matn o'qilmoqda…");
        this._startOcr(content, scale, width, height);
    }

    _startOcr(content, scale, width, height) {
        this._cancellable = new Gio.Cancellable();
        const cancellable = this._cancellable;

        captureFrozenFrame(content, scale, width, height, (path, captureError) => {
            if (cancellable.is_cancelled() || !this.isOpen)
                return;
            if (captureError) {
                this._glow?.setState('error');
                this._showPill(captureError);
                return;
            }

            this._framePath = path;
            recognizeWords(path, this._getLanguages(), (words, ocrError) => {
                deleteFrame(path);
                this._framePath = null;

                if (cancellable.is_cancelled() || !this.isOpen)
                    return;
                if (ocrError) {
                    this._glow?.setState('error');
                    this._showPill(ocrError);
                    return;
                }
                this._attachTextLayer(words, scale, width, height);
            }, cancellable);
        });
    }

    _attachTextLayer(words, scale, width, height) {
        if (words.length === 0) {
            this._glow?.setState('error');
            this._showPill('Matn topilmadi. Esc — chiqish.');
            return;
        }

        this._textLayer = new TextSelectionLayer(words, scale);
        this._textLayer.set_position(0, 0);
        this._textLayer.set_size(width, height);
        this._container.add_child(this._textLayer);
        this._textLayer.connect('selection-changed', () => this._onSelectionChanged());

        // Matn qatlami halqani bosib qolmasligi uchun halqa ustga ko'tariladi.
        // Amal paneli esa keyin qo'shiladi, shuning uchun u halqadan ustda bo'ladi.
        this._glow?.raiseTop();
        this._glow?.setState('ready');

        try {
            global.display.set_cursor(Meta.Cursor.IBEAM);
        } catch (e) {
            // Muhim emas — belgilash shundoq ham ishlaydi.
        }

        this._showPill(`${words.length} so'z topildi — sudrab belgilang`);
        this._hidePillLater();
    }

    _onSelectionChanged() {
        const text = this._textLayer?.getSelectedText() ?? '';
        if (!text) {
            this._bar?.hide();
            return;
        }
        this._showBar(this._textLayer.getSelectionBounds());
    }

    _showBar(bounds) {
        if (!this._bar) {
            this._bar = new St.BoxLayout({style: BAR_STYLE, vertical: false});

            const copyButton = new St.Button({
                label: 'Nusxalash',
                style: BUTTON_STYLE,
                can_focus: true,
            });
            copyButton.connect('clicked', () => {
                this._copySelection();
                this.close();
            });

            const translateButton = new St.Button({
                label: 'Tarjima qil',
                style: BUTTON_STYLE,
                can_focus: true,
            });
            translateButton.connect('clicked', () => {
                const text = this._textLayer?.getSelectedText() ?? '';
                this.close();
                if (text)
                    this._onTranslate(text);
            });

            this._bar.add_child(copyButton);
            this._bar.add_child(translateButton);
            this._container.add_child(this._bar);
        }

        this._bar.show();
        if (!bounds)
            return;

        // Panelni belgilangan matn ostiga, ekran chegarasidan chiqmaydigan qilib qo'yamiz.
        const [, barWidth] = this._bar.get_preferred_width(-1);
        const [, barHeight] = this._bar.get_preferred_height(-1);
        let x = bounds.x + bounds.width / 2 - barWidth / 2;
        let y = bounds.y + bounds.height + BAR_GAP;

        x = Math.max(BAR_GAP, Math.min(x, global.stage.width - barWidth - BAR_GAP));
        if (y + barHeight > global.stage.height - BAR_GAP)
            y = Math.max(BAR_GAP, bounds.y - barHeight - BAR_GAP);

        this._bar.set_position(Math.round(x), Math.round(y));
    }

    _copySelection() {
        const text = this._textLayer?.getSelectedText() ?? '';
        if (text)
            St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, text);
    }

    _showPill(message) {
        if (!this._pill) {
            this._pill = new St.Label({style: PILL_STYLE});
            this._container.add_child(this._pill);
        }
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
            this._copySelection();
            this.close();
            return Clutter.EVENT_STOP;
        }
        if (ctrl && (symbol === Clutter.KEY_a || symbol === Clutter.KEY_A)) {
            this._textLayer?.selectAll();
            return Clutter.EVENT_STOP;
        }
        return Clutter.EVENT_PROPAGATE;
    }
}
