/**
 * Maydon tanlash qatlami (Taqdimot qatlami — mantiq yo'q, faqat tanlash).
 *
 * Qotirilgan ekranda sichqoncha bilan to'rtburchak chiziladi: tanlangan
 * joy ochiq qoladi, atrofi qoraytiriladi — shunda nima o'qilishi aniq
 * ko'rinadi. Tanlash tugagach `region-selected` signali chiqadi.
 *
 * Nega butun ekran emas, maydon: butun ekranni o'qiganda sarlavha,
 * aktyor ismlari va boshqa interfeys matni aralashib ketadi, ustiga
 * 1920x1080 ni o'qish sekin. Maydon tanlansa natija toza va tez bo'ladi.
 *
 * Arzonlik: qoraytirish uchun blur emas, 4 ta oddiy to'rtburchak
 * ishlatiladi (iGPU VRAM cheklangan mashina).
 */

import GObject from 'gi://GObject';
import St from 'gi://St';
import Clutter from 'gi://Clutter';

import {normalizeRect, clampRect, isUsableRegion} from './region-geometry.js';

/** Tanlovdan tashqaridagi qoraytirish. */
const DIM_STYLE = 'background-color: rgba(0, 0, 0, 0.55);';

/** Tanlangan maydon chegarasi. */
const SELECTION_STYLE =
    'border: 2px solid rgba(53, 132, 228, 0.95); ' +
    'background-color: rgba(53, 132, 228, 0.10);';

export const RegionSelector = GObject.registerClass({
    GTypeName: 'QuickTranslateRegionSelector',
    Signals: {
        /** Yaroqli maydon tanlandi. Tafsilot `lastRegion` dan olinadi. */
        'region-selected': {},
    },
}, class RegionSelector extends St.Widget {
    _init(width, height) {
        super._init({reactive: true, x: 0, y: 0, width, height});

        this._bounds = {width, height};
        this._startX = 0;
        this._startY = 0;
        this._dragging = false;
        this._enabled = true;

        /** Oxirgi yaroqli tanlov (stage koordinatasida). */
        this.lastRegion = null;

        // Tanlovdan tashqarini qoraytiruvchi 4 ta to'rtburchak:
        // yuqori, pastki, chap, o'ng. Boshida butun ekran qoraytirilgan.
        this._dims = [];
        for (let i = 0; i < 4; i++) {
            const dim = new St.Widget({style: DIM_STYLE, reactive: false});
            this.add_child(dim);
            this._dims.push(dim);
        }

        this._frame = new St.Widget({style: SELECTION_STYLE, reactive: false, visible: false});
        this.add_child(this._frame);

        this._showDimOnly();

        this.connect('button-press-event', this._onPress.bind(this));
        this.connect('motion-event', this._onMotion.bind(this));
        this.connect('button-release-event', this._onRelease.bind(this));
    }

    /** OCR ketayotganda yangi tanlov boshlanmasligi uchun. */
    setEnabled(enabled) {
        this._enabled = enabled;
        if (!enabled)
            this._dragging = false;
    }

    /** Butun ekranni tanlaydi (Ctrl+A). */
    selectAll() {
        if (!this._enabled)
            return;
        this.lastRegion = {x: 0, y: 0, width: this._bounds.width, height: this._bounds.height};
        this._drawRegion(this.lastRegion);
        this.emit('region-selected');
    }

    _onPress(actor, event) {
        if (!this._enabled || event.get_button() !== Clutter.BUTTON_PRIMARY)
            return Clutter.EVENT_PROPAGATE;

        const [x, y] = event.get_coords();
        this._startX = x;
        this._startY = y;
        this._dragging = true;
        this._drawRegion({x, y, width: 0, height: 0});
        return Clutter.EVENT_STOP;
    }

    _onMotion(actor, event) {
        if (!this._dragging)
            return Clutter.EVENT_PROPAGATE;

        const [x, y] = event.get_coords();
        this._drawRegion(this._regionFor(x, y));
        return Clutter.EVENT_STOP;
    }

    _onRelease(actor, event) {
        if (!this._dragging)
            return Clutter.EVENT_PROPAGATE;
        this._dragging = false;

        const [x, y] = event.get_coords();
        const region = this._regionFor(x, y);

        // Tasodifiy bosish maydon emas — avvalgi holatga qaytamiz.
        if (!isUsableRegion(region)) {
            this.lastRegion = null;
            this._showDimOnly();
            return Clutter.EVENT_STOP;
        }

        this.lastRegion = region;
        this._drawRegion(region);
        this.emit('region-selected');
        return Clutter.EVENT_STOP;
    }

    _regionFor(x, y) {
        return clampRect(normalizeRect(this._startX, this._startY, x, y), this._bounds);
    }

    /** Hali tanlov yo'q: butun ekran qoraytirilgan. */
    _showDimOnly() {
        this._frame.hide();
        const {width, height} = this._bounds;
        this._placeDims({x: 0, y: 0, width: 0, height: 0});
        // Birinchi to'rtburchak butun ekranni qoplaydi, qolganlari bo'sh.
        this._dims[0].set_position(0, 0);
        this._dims[0].set_size(width, height);
        for (let i = 1; i < 4; i++)
            this._dims[i].set_size(0, 0);
    }

    _drawRegion(region) {
        this._placeDims(region);
        this._frame.set_position(region.x, region.y);
        this._frame.set_size(region.width, region.height);
        this._frame.show();
    }

    /** Tanlov atrofidagi 4 ta qoraytirish to'rtburchagini joylashtiradi. */
    _placeDims(region) {
        const {width, height} = this._bounds;
        const right = region.x + region.width;
        const bottom = region.y + region.height;

        const boxes = [
            {x: 0, y: 0, width, height: region.y},                              // yuqori
            {x: 0, y: bottom, width, height: Math.max(0, height - bottom)},     // pastki
            {x: 0, y: region.y, width: region.x, height: region.height},        // chap
            {x: right, y: region.y, width: Math.max(0, width - right), height: region.height},
        ];

        boxes.forEach((box, i) => {
            this._dims[i].set_position(box.x, box.y);
            this._dims[i].set_size(Math.max(0, box.width), Math.max(0, box.height));
        });
    }
});
