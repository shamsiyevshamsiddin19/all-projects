import Gio from 'gi://Gio';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import {QuickTranslatePopup} from './popup.js';
import {getSelection, getTruePointerCoords} from './selection-service.js';
import {requestMultiTranslation} from './translation-service.js';
import {FreezeOverlay} from './freeze-service.js';

/** Tarjimaga yuboriladigan maksimal matn uzunligi (belgi). */
const MAX_TEXT_LENGTH = 3000;

export default class QuickTranslateExtension extends Extension {
    enable() {
        this._settings = this.getSettings();
        this._request = null;
        this._popup = null;
        this._selectionPending = false;
        this._freeze = null;

        Main.wm.addKeybinding(
            'toggle-popup',
            this._settings,
            Meta.KeyBindingFlags.NONE,
            Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW,
            () => this._toggle()
        );

        // Ekranni qotirish qismi alohida izolyatsiya qilinadi: unda xato
        // bo'lsa ham enable() uzilmasligi va Ctrl+Alt+Z ishlashda davom
        // etishi kerak (bitta istisno butun kengaytmani o'chirib qo'yadi).
        try {
            this._freeze = new FreezeOverlay(
                text => this._translateText(text),
                () => this._settings.get_string('ocr-languages'),
                () => this._settings.get_boolean('glow-enabled')
            );
            // POPUP ham kiritiladi: overlay ochilganda modal POPUP rejimiga
            // o'tadi, shu rejim ro'yxatda bo'lmasa Ctrl+Alt+X qayta bosilganda
            // ishlamay qolar va overlayni faqat Esc bilan yopish mumkin bo'lardi.
            const action = Main.wm.addKeybinding(
                'freeze-ocr',
                this._settings,
                Meta.KeyBindingFlags.NONE,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW | Shell.ActionMode.POPUP,
                () => this._toggleFreeze()
            );
            // Jim muvaffaqiyatsizlik ehtimoli bor: schema kaliti ko'rinmasa
            // addKeybinding istisno tashlamaydi, shunchaki 0 qaytaradi.
            if (!action) {
                console.warn('[QuickTranslate] freeze-ocr yorligi royxatga olinmadi ' +
                    '(Shell eski schemani ishlatayotgan bolishi mumkin — logout/login kerak)');
            }
        } catch (e) {
            console.error(`[QuickTranslate] Ekranni qotirish yoqilmadi: ${e.message}`);
            this._freeze = null;
        }
    }

    disable() {
        Main.wm.removeKeybinding('toggle-popup');

        try {
            Main.wm.removeKeybinding('freeze-ocr');
        } catch (e) {
            // Yorliq ro'yxatga olinmagan bo'lsa muammo emas.
        }
        this._freeze?.destroy();
        this._freeze = null;

        this._selectionPending = false;
        this._request?.cancel();
        this._request = null;
        this._popup?.destroy(true);
        this._popup = null;
        this._settings = null;
    }

    /** Ctrl+Alt+X — ekranni qotirib, rasmdagi matnni belgilash. */
    _toggleFreeze() {
        if (!this._freeze)
            return;
        try {
            if (this._freeze.isOpen)
                this._freeze.close();
            else
                this._freeze.open();
        } catch (e) {
            console.error(`[QuickTranslate] Qotirish xatosi: ${e.message}\n${e.stack}`);
        }
    }

    /** Ctrl+Alt+Z — sichqoncha bilan belgilangan matnni tarjima qilish. */
    _toggle() {
        if (this._popup && !this._popup._destroyed) {
            this._popup.destroy();
            this._popup = null;
            return;
        }
        if (this._selectionPending) {
            this._request?.cancel();
            this._selectionPending = false;
            return;
        }

        const [x, y] = getTruePointerCoords();
        this._request?.cancel();
        const request = new Gio.Cancellable();
        this._request = request;
        this._selectionPending = true;

        getSelection((text, selectionError) => {
            if (request.is_cancelled() || this._request !== request) return;
            this._selectionPending = false;
            this._showTranslation(x, y, text, request,
                selectionError || 'Avval matnni sichqoncha bilan belgilang.');
        }, request);
    }

    /**
     * OCR natijasini tarjima qiladi: belgilash bosqichi yo'q, matn tayyor.
     * Oyna kursor turgan joyda chiqadi.
     *
     * Bu yo'lda overlay mediani pauzada qoldirib yopiladi, shuning uchun
     * tarjima kartasi yopilgandagina video davom etadi — foydalanuvchi
     * tarjimani o'qiyotganda video orqada o'ynab ketmaydi.
     */
    _translateText(text) {
        const [x, y] = getTruePointerCoords();
        this._request?.cancel();
        const request = new Gio.Cancellable();
        this._request = request;
        this._showTranslation(x, y, text, request, 'Matn bo‘sh.');
        this._popup?.setOnClosed(() => this._freeze?.resumeMedia());
    }

    /**
     * Oynani ochib tarjima so'rovini yuboradi.
     * Ikki yo'l (belgilangan matn va OCR) shu yerda birlashadi — tarjima
     * mantiqi bitta joyda turadi.
     *
     * @param {number} x             oyna joyi
     * @param {number} y             oyna joyi
     * @param {string} text          tarjima qilinadigan matn
     * @param {Gio.Cancellable} request
     * @param {string} emptyMessage  matn bo'sh bo'lsa ko'rsatiladigan xabar
     */
    _showTranslation(x, y, text, request, emptyMessage) {
        const popup = new QuickTranslatePopup(x, y, text || '');
        this._popup = popup;

        if (!text) {
            popup.setError(emptyMessage);
            return;
        }
        if (!popup.startRequest(request))
            return;
        if (Array.from(text).length > MAX_TEXT_LENGTH) {
            popup.setError(`Matn juda uzun. ${MAX_TEXT_LENGTH} belgigacha bo‘lgan qismini tanlang.`);
            return;
        }

        requestMultiTranslation(text, (result, error) => {
            if (this._popup !== popup || popup._destroyed) return;
            if (error || !result) popup.setError(error || 'Tarjima olinmadi.');
            else popup.setResult(result);
        }, request);
    }
}
