/**
 * Live Text belgilash qatlami (Taqdimot qatlami — mantiq yo'q, faqat tanlash).
 *
 * OCR qaytargan so'z to'rtburchaklari ustida brauzerdagidek tabiiy belgilash
 * beradi: bosib sudraysiz, o'qish tartibida boshidan oxirigacha belgilanadi.
 *
 * To'rtburchak kesishishi emas, **o'qish tartibi** ishlatiladi: anchor so'zdan
 * joriy so'zgacha oradagi hammasi tanlanadi. Shuning uchun ikki satrni qiyshiq
 * sudrab belgilaganda ham matn to'g'ri, uzilmasdan chiqadi.
 */

import GObject from 'gi://GObject';
import St from 'gi://St';
import Clutter from 'gi://Clutter';

import {joinWords} from './tsv-parser.js';

/** Belgilangan so'z ustidagi yoritish rangi (GNOME ko'k, yarim shaffof). */
const HIGHLIGHT_COLOR = 'rgba(53, 132, 228, 0.40)';

/** So'z to'rtburchagini shu qadar px kengaytirib tegish maydonini oshiramiz. */
const HIT_PADDING = 2;

export const TextSelectionLayer = GObject.registerClass({
    GTypeName: 'QuickTranslateTextSelectionLayer',
    Signals: {
        'selection-changed': {},
    },
}, class TextSelectionLayer extends St.Widget {
    /**
     * @param {object[]} words  ocr-service.js qaytargan so'zlar (piksel koordinatada)
     * @param {number} scale    piksel/stage nisbati (HiDPI uchun)
     */
    _init(words, scale) {
        super._init({
            reactive: true,
            x_expand: true,
            y_expand: true,
        });

        const safeScale = Number.isFinite(scale) && scale > 0 ? scale : 1;

        /** So'zlar stage koordinatasida — ekranda ko'rinayotgan o'lchovda. */
        this._words = words.map(word => ({
            text: word.text,
            line: word.line,
            index: word.index,
            x: word.x / safeScale,
            y: word.y / safeScale,
            w: word.w / safeScale,
            h: word.h / safeScale,
        }));

        this._anchorIndex = -1;
        this._focusIndex = -1;
        this._dragging = false;
        this._highlights = [];

        this.connect('button-press-event', this._onPress.bind(this));
        this.connect('motion-event', this._onMotion.bind(this));
        this.connect('button-release-event', this._onRelease.bind(this));
        this.connect('destroy', this._onDestroy.bind(this));
    }

    /** OCR hech narsa topmaganini bildiradi. */
    get isEmpty() {
        return this._words.length === 0;
    }

    get hasSelection() {
        return this._anchorIndex >= 0 && this._focusIndex >= 0;
    }

    /**
     * Belgilangan matn. Bir satr ichidagi so'zlar bo'sh joy bilan, satrlar
     * orasi yangi qator bilan ajratiladi — subtitr ikki satr bo'lsa ham
     * o'qiladigan ko'rinishda chiqadi.
     */
    getSelectedText() {
        return joinWords(this._selectedWords());
    }

    /** Belgilangan sohaning stage'dagi chegarasi — amal panelini joylash uchun. */
    getSelectionBounds() {
        const selected = this._selectedWords();
        if (selected.length === 0)
            return null;

        let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
        for (const word of selected) {
            x1 = Math.min(x1, word.x);
            y1 = Math.min(y1, word.y);
            x2 = Math.max(x2, word.x + word.w);
            y2 = Math.max(y2, word.y + word.h);
        }
        return {x: x1, y: y1, width: x2 - x1, height: y2 - y1};
    }

    /** Ekrandagi butun matnni belgilaydi (Ctrl+A). */
    selectAll() {
        if (this.isEmpty)
            return;
        this._anchorIndex = 0;
        this._focusIndex = this._words.length - 1;
        this._redrawHighlights();
        this.emit('selection-changed');
    }

    clearSelection() {
        this._anchorIndex = -1;
        this._focusIndex = -1;
        this._redrawHighlights();
        this.emit('selection-changed');
    }

    _onPress(actor, event) {
        if (event.get_button() !== Clutter.BUTTON_PRIMARY)
            return Clutter.EVENT_PROPAGATE;

        const [x, y] = event.get_coords();
        const word = this._nearestWord(x, y);
        if (!word)
            return Clutter.EVENT_STOP;

        this._dragging = true;
        this._anchorIndex = word.index;
        this._focusIndex = word.index;
        this._redrawHighlights();
        this.emit('selection-changed');
        return Clutter.EVENT_STOP;
    }

    _onMotion(actor, event) {
        if (!this._dragging)
            return Clutter.EVENT_PROPAGATE;

        const [x, y] = event.get_coords();
        const word = this._nearestWord(x, y);
        if (!word || word.index === this._focusIndex)
            return Clutter.EVENT_STOP;

        this._focusIndex = word.index;
        this._redrawHighlights();
        this.emit('selection-changed');
        return Clutter.EVENT_STOP;
    }

    _onRelease(actor, event) {
        if (!this._dragging)
            return Clutter.EVENT_PROPAGATE;
        this._dragging = false;
        this.emit('selection-changed');
        return Clutter.EVENT_STOP;
    }

    _onDestroy() {
        this._clearHighlightActors();
        this._words = [];
    }

    /** Anchor va fokus orasidagi so'zlar, o'qish tartibida. */
    _selectedWords() {
        if (!this.hasSelection)
            return [];
        const from = Math.min(this._anchorIndex, this._focusIndex);
        const to = Math.max(this._anchorIndex, this._focusIndex);
        return this._words.slice(from, to + 1);
    }

    /**
     * Nuqtaga eng yaqin so'z. To'rtburchak ichida bo'lsa masofa 0,
     * aks holda to'rtburchakka eng qisqa masofa hisoblanadi — shuning uchun
     * so'zlar orasidagi bo'sh joyga bosilsa ham eng mantiqiy so'z tanlanadi.
     */
    _nearestWord(x, y) {
        let best = null;
        let bestDistance = Infinity;

        for (const word of this._words) {
            const dx = Math.max(word.x - HIT_PADDING - x, 0, x - (word.x + word.w + HIT_PADDING));
            const dy = Math.max(word.y - HIT_PADDING - y, 0, y - (word.y + word.h + HIT_PADDING));
            const distance = dx * dx + dy * dy;
            if (distance < bestDistance) {
                bestDistance = distance;
                best = word;
                if (distance === 0)
                    break;
            }
        }
        return best;
    }

    /**
     * Yoritishni qayta chizadi. Bir satrdagi so'zlar bitta to'rtburchakka
     * qo'shiladi: shunda belgilash uzuq-yuluq emas, yaxlit ko'rinadi va
     * ekranda kerakdan ortiq aktor paydo bo'lmaydi (VRAM tejaladi).
     */
    _redrawHighlights() {
        this._clearHighlightActors();

        const selected = this._selectedWords();
        if (selected.length === 0)
            return;

        const perLine = new Map();
        for (const word of selected) {
            const box = perLine.get(word.line);
            if (!box) {
                perLine.set(word.line, {x1: word.x, y1: word.y, x2: word.x + word.w, y2: word.y + word.h});
                continue;
            }
            box.x1 = Math.min(box.x1, word.x);
            box.y1 = Math.min(box.y1, word.y);
            box.x2 = Math.max(box.x2, word.x + word.w);
            box.y2 = Math.max(box.y2, word.y + word.h);
        }

        for (const box of perLine.values()) {
            const highlight = new St.Widget({
                style: `background-color: ${HIGHLIGHT_COLOR}; border-radius: 3px;`,
                x: Math.round(box.x1) - HIT_PADDING,
                y: Math.round(box.y1) - HIT_PADDING,
                width: Math.round(box.x2 - box.x1) + HIT_PADDING * 2,
                height: Math.round(box.y2 - box.y1) + HIT_PADDING * 2,
                reactive: false,
            });
            this.add_child(highlight);
            this._highlights.push(highlight);
        }
    }

    _clearHighlightActors() {
        for (const highlight of this._highlights)
            highlight.destroy();
        this._highlights = [];
    }
});
