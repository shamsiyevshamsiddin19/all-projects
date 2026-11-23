/**
 * Media pauza xizmati (Command qatlami — faqat yon ta'sir, UI yo'q).
 *
 * MPRIS2 standarti orqali o'ynayotgan pleyerlarni to'xtatadi va keyin
 * qaytadan davom ettiradi. `playerctl` kerak emas: D-Bus to'g'ridan-to'g'ri
 * chaqiriladi. Chrome, Firefox, Celluloid, Amberol, VLC, mpv — hammasi
 * MPRIS'ni qo'llaydi.
 */

import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

const MPRIS_PREFIX = 'org.mpris.MediaPlayer2.';
const MPRIS_PATH = '/org/mpris/MediaPlayer2';
const PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player';
const PROPS_IFACE = 'org.freedesktop.DBus.Properties';

/** D-Bus chaqiruvi uchun maksimal kutish (ms). Osilgan pleyer bizni bloklamasin. */
const CALL_TIMEOUT_MS = 500;

export class MediaPauseService {
    constructor() {
        /** @type {string[]} Biz to'xtatgan pleyerlar — chiqishda faqat shular davom etadi. */
        this._pausedNames = [];
    }

    /**
     * Hozir o'ynayotgan barcha MPRIS pleyerlarini pauzaga qo'yadi.
     * Allaqachon to'xtab turganlarga tegmaydi, shuning uchun chiqishda
     * foydalanuvchi o'zi to'xtatgan video kutilmaganda o'ynab ketmaydi.
     */
    pausePlaying() {
        this._pausedNames = [];
        this._listNames(names => {
            for (const name of names.filter(n => n.startsWith(MPRIS_PREFIX)))
                this._pauseIfPlaying(name);
        });
    }

    /** Faqat o'zimiz to'xtatgan pleyerlarni qaytadan davom ettiradi. */
    resume() {
        const names = this._pausedNames;
        this._pausedNames = [];
        for (const name of names)
            this._callPlayer(name, 'Play');
    }

    /** Hech narsani qaytarmasdan holatni tozalaydi (kengaytma o'chganda). */
    forget() {
        this._pausedNames = [];
    }

    _listNames(callback) {
        Gio.DBus.session.call(
            'org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
            'ListNames', null, new GLib.VariantType('(as)'),
            Gio.DBusCallFlags.NONE, CALL_TIMEOUT_MS, null,
            (bus, res) => {
                try {
                    const [names] = bus.call_finish(res).deepUnpack();
                    callback(names);
                } catch (e) {
                    console.warn(`[QuickTranslate] MPRIS ro'yxati olinmadi: ${e.message}`);
                }
            });
    }

    _pauseIfPlaying(name) {
        Gio.DBus.session.call(
            name, MPRIS_PATH, PROPS_IFACE, 'Get',
            new GLib.Variant('(ss)', [PLAYER_IFACE, 'PlaybackStatus']),
            new GLib.VariantType('(v)'),
            Gio.DBusCallFlags.NONE, CALL_TIMEOUT_MS, null,
            (bus, res) => {
                let status = '';
                try {
                    const [variant] = bus.call_finish(res).deepUnpack();
                    status = variant.deepUnpack();
                } catch (e) {
                    return; // Pleyer javob bermadi — e'tiborsiz qoldiramiz.
                }
                if (status !== 'Playing')
                    return;
                this._pausedNames.push(name);
                this._callPlayer(name, 'Pause');
            });
    }

    _callPlayer(name, method) {
        Gio.DBus.session.call(
            name, MPRIS_PATH, PLAYER_IFACE, method, null, null,
            Gio.DBusCallFlags.NONE, CALL_TIMEOUT_MS, null,
            (bus, res) => {
                try {
                    bus.call_finish(res);
                } catch (e) {
                    console.warn(`[QuickTranslate] ${name} -> ${method} bajarilmadi: ${e.message}`);
                }
            });
    }
}
