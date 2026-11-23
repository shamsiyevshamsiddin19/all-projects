import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Clutter from 'gi://Clutter';
import St from 'gi://St';
import Shell from 'gi://Shell';
import Pango from 'gi://Pango';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {GrabHelper} from 'resource:///org/gnome/shell/ui/grabHelper.js';
import {englishLookup} from './example-utils.js';
import {VocabularyStore, Pronunciation} from './learning-services.js';
import {fetchDictionaryExample, fetchOne} from './translation-service.js';

export class QuickTranslatePopup {
    constructor(pointerX, pointerY, originalText) {
        let mon = Main.layoutManager.primaryMonitor;
        this.pointerX = Number.isFinite(pointerX) ? pointerX : Math.round(mon.x + mon.width / 2);
        this.pointerY = Number.isFinite(pointerY) ? pointerY : Math.round(mon.y + mon.height / 2);
        this.originalText = originalText;
        this._timerId = null;
        this._stageClickId = null;
        this._stageKeyId = null;
        this._copiedText = '';
        this._destroyed = false;
        this._ready = false;
        this.state = 'loading';
        this._voice = new Pronunciation();
        this._store = new VocabularyStore();

        this._createWidget();
        this._positionWidget();
        this._setupEvents();
        // GNOME o'zining popup mexanizmi fokus va tashqi bosishlarni boshqaradi.
        this._grabHelper = new GrabHelper(this._overlay, {
            // Popup rejimi Print Screen kabi ruxsat etilgan tizim tugmalarini saqlaydi.
            actionMode: Shell.ActionMode.POPUP,
        });
        if (!this._grabHelper.grab({
            actor: this.actor,
            focus: this.actor,
            onUngrab: () => this.destroy(),
        })) {
            this.destroy(true);
            Main.notify('Tezkor tarjimon', 'Oyna ochilmadi. Boshqa menyuni yopib, qayta urinib ko‘ring.');
        }
    }

    _createWidget() {
        this.actor = new St.BoxLayout({
            vertical: true,
            reactive: true,
            can_focus: true,
            track_hover: true,
            width: 480,
            height: 300,
        });
        this.actor.set_size(480, 300);

        // Standard plastic bank card proportions: 480x300 px (1.6:1 aspect ratio), OpenAI dark theme
        this.actor.set_style(
            'background-color: #121212; ' +
            'border: 1px solid rgba(255, 255, 255, 0.14); ' +
            'border-radius: 18px; ' +
            'padding: 24px 28px; ' +
            'box-shadow: 0 24px 60px rgba(0, 0, 0, 0.9); ' +
            'min-width: 480px; ' +
            'max-width: 480px; ' +
            'min-height: 300px; ' +
            'max-height: 300px;'
        );

        // Header: Pill + Close button
        let header = new St.BoxLayout({ vertical: false, style: 'margin-bottom: 16px;' });

        this.pill = new St.Label({
            text: 'TRANSLATING',
            style: 'background-color: #242424; color: #a1a1aa; font-size: 11px; font-weight: bold; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.1); padding: 4px 12px; letter-spacing: 0.5px;'
        });
        header.add_child(this.pill);

        let spacer = new St.Widget({ x_expand: true });
        header.add_child(spacer);

        this.closeBtn = new St.Button({
            label: '×',
            reactive: true,
            style: 'color: #71717a; font-size: 22px; font-weight: bold; padding: 0 6px;'
        });
        this.closeBtn.connect('clicked', () => this.destroy());
        header.add_child(this.closeBtn);
        this.actor.add_child(header);

        // Center section: container for translations & original
        let bodyBox = new St.BoxLayout({ vertical: true, y_expand: true, x_expand: true });

        // Item 1 (Primary / RU)
        this.row1 = new St.BoxLayout({ vertical: false, style: 'margin-bottom: 12px;' });
        this.tag1 = new St.Button({
            label: '',
            can_focus: true,
            reactive: false,
            visible: false,
            style: 'background-color: #202024; color: #94a3b8; font-size: 11px; font-weight: 700; border-radius: 5px; border: 1px solid #33333f; padding: 2px 7px; margin-right: 12px; margin-top: 4px;'
        });
        this.row1.add_child(this.tag1);
        this.tag1.connect('clicked', () => this._showExample(0));

        this.trans1 = new St.Label({
            text: '...',
            style: 'color: #ffffff; font-size: 22px; font-weight: 600; line-height: 1.3;'
        });
        this.trans1.clutter_text.line_wrap = true;
        this.trans1.x_expand = true;
        this.trans1.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        this.row1.add_child(this.trans1);
        this.speak1 = this._iconButton('audio-volume-high-symbolic', 'Birinchi tarjimani tinglash',
            () => this._speak(this._items?.[0]));
        this.speak1.reactive = false;
        this.row1.add_child(this.speak1);
        bodyBox.add_child(this.row1);

        // Item 2 (Secondary / EN)
        this.row2 = new St.BoxLayout({ vertical: false, visible: false, style: 'margin-bottom: 12px;' });
        this.tag2 = new St.Button({
            label: '',
            can_focus: true,
            reactive: false,
            style: 'background-color: #202024; color: #94a3b8; font-size: 11px; font-weight: 700; border-radius: 5px; border: 1px solid #33333f; padding: 2px 7px; margin-right: 12px; margin-top: 4px;'
        });
        this.row2.add_child(this.tag2);
        this.tag2.connect('clicked', () => this._showExample(1));

        this.trans2 = new St.Label({
            text: '',
            style: 'color: #e4e4e7; font-size: 20px; font-weight: 500; line-height: 1.3;'
        });
        this.trans2.clutter_text.line_wrap = true;
        this.trans2.x_expand = true;
        this.trans2.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        this.row2.add_child(this.trans2);
        this.speak2 = this._iconButton('audio-volume-high-symbolic', 'Ikkinchi tarjimani tinglash',
            () => this._speak(this._items?.[1]));
        this.speak2.reactive = false;
        this.row2.add_child(this.speak2);
        bodyBox.add_child(this.row2);

        this.exampleLabel = new St.Label({
            text: '', visible: false, x_expand: true,
            style: 'color: #b4b4b4; font-size: 15px; margin-top: 8px; margin-bottom: 12px;',
        });
        this.exampleLabel.clutter_text.line_wrap = true;
        this.exampleLabel.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        bodyBox.add_child(this.exampleLabel);
        this.meaningLabel = new St.Label({
            text: '', visible: false, x_expand: true,
            style: 'color: #929292; font-size: 12px; margin-bottom: 10px;',
        });
        this.meaningLabel.clutter_text.line_wrap = true;
        this.meaningLabel.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        bodyBox.add_child(this.meaningLabel);
        this.exampleSpeak = this._iconButton('audio-volume-high-symbolic', 'Misol gapni tinglash',
            () => this._speak(this._activeExample));
        this.exampleSpeak.visible = false;
        bodyBox.add_child(this.exampleSpeak);

        // Body spacer to push original to bottom
        let midSpacer = new St.Widget({ y_expand: true });
        bodyBox.add_child(midSpacer);

        // Original snippet
        let origSnippet = (this.originalText || '').replace(/\s+/g, ' ');
        if (origSnippet.length > 80) origSnippet = origSnippet.slice(0, 77) + '...';
        this.origLabel = new St.Label({
            text: origSnippet,
            style: 'color: #71717a; font-size: 13px; line-height: 1.3;'
        });
        this.origLabel.clutter_text.line_wrap = true;
        this.origLabel.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        this.origLabel.clutter_text.ellipsize = Pango.EllipsizeMode.END;
        bodyBox.add_child(this.origLabel);

        const scroll = new St.ScrollView({x_expand: true, y_expand: true});
        scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        scroll.add_child(bodyBox);
        this.actor.add_child(scroll);
        this._mainScroll = scroll;

        this._libraryBody = new St.BoxLayout({vertical: true, x_expand: true});
        this._libraryScroll = new St.ScrollView({visible: false, x_expand: true, y_expand: true});
        this._libraryScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this._libraryScroll.add_child(this._libraryBody);
        this.actor.add_child(this._libraryScroll);

        this._statusLabel = new St.Label({text: '', visible: false,
            style: 'font-size: 11px; color: #b4b4b4;'});
        this._statusLabel.clutter_text.line_wrap = true;
        this.actor.add_child(this._statusLabel);

        // Bottom Row: Hint + Copy button
        this.bottomRow = new St.BoxLayout({ vertical: false, style: 'margin-top: 14px;' });

        this.saveBtn = this._textButton('Saqlash', () => this._saveWord());
        this.saveBtn.reactive = false;
        this.bottomRow.add_child(this.saveBtn);
        this.libraryBtn = this._textButton('Lug‘at', () => this._toggleLibrary());
        this.bottomRow.add_child(this.libraryBtn);

        let bSpacer = new St.Widget({ x_expand: true });
        this.bottomRow.add_child(bSpacer);

        this.copyBtn = new St.Button({
            label: 'Copy',
            reactive: false,
            can_focus: true,
            style: 'background-color: #27272a; color: #f4f4f5; font-size: 12px; font-weight: 600; border-radius: 8px; border: 1px solid #3f3f46; padding: 6px 18px;'
        });
        this.copyBtn.connect('clicked', () => this._copy());
        this.bottomRow.add_child(this.copyBtn);
        this.actor.add_child(this.bottomRow);

        this._overlay = new St.Widget({reactive: true, can_focus: true});
        this._overlay.add_constraint(new Clutter.BindConstraint({
            source: global.stage,
            coordinate: Clutter.BindCoordinate.ALL,
        }));
        this._overlay.add_child(this.actor);
        Main.layoutManager.addTopChrome(this._overlay);
        this.actor.opacity = 0;
        this.actor.ease({
            opacity: 255,
            duration: 100,
            mode: Clutter.AnimationMode.EASE_OUT_QUAD
        });
    }

    _positionWidget() {
        let monitor = Main.layoutManager.primaryMonitor;
        for (let m of Main.layoutManager.monitors) {
            if (this.pointerX >= m.x && this.pointerX < m.x + m.width &&
                this.pointerY >= m.y && this.pointerY < m.y + m.height) {
                monitor = m;
                break;
            }
        }

        let w = 480;
        let h = 300;

        // Center horizontally on pointer, position right above cursor
        let posX = Math.round(this.pointerX - w / 2);
        let posY = Math.round(this.pointerY - h - 16);

        // If not enough room above cursor, place directly below cursor
        if (posY < monitor.y + 40) {
            posY = Math.round(this.pointerY + 24);
        }

        // Clamp to monitor boundaries
        if (posX + w > monitor.x + monitor.width - 20) {
            posX = monitor.x + monitor.width - w - 20;
        }
        if (posX < monitor.x + 20) {
            posX = monitor.x + 20;
        }
        if (posY + h > monitor.y + monitor.height - 20) {
            posY = monitor.y + monitor.height - h - 20;
        }
        if (posY < monitor.y + 36) {
            posY = monitor.y + 36;
        }

        this.actor.set_position(posX, posY);
    }

    setResult(resultData) {
        if (this._destroyed) return;
        this._clearDeadline();
        this.state = 'ready';
        if (!resultData || !resultData.items || resultData.items.length === 0) {
            this.setError('No translation found');
            return;
        }

        let src = resultData.src || 'AUTO';
        let items = resultData.items;
        this._resultSource = src;
        this._savedCurrent = false;
        this._voice?.stop();
        this._speechPlaying = false;
        this._meaningCache = new Map();
        this.meaningLabel.visible = false;
        this.exampleLabel.visible = false;
        this.exampleSpeak.visible = false;
        this._activeExample = null;
        this.speak1.reactive = Boolean(items[0]?.text && ['RU', 'EN'].includes(items[0]?.tag));
        this.speak2.reactive = Boolean(items[1]?.text && ['RU', 'EN'].includes(items[1]?.tag));
        this.saveBtn.reactive = items.every(item => item.text && !item.error);
        this.saveBtn.set_label('Saqlash');
        this._items = items;
        this._exampleCache = new Map();
        this.tag1.reactive = Boolean(items[0]?.text && !items[0]?.error);
        this.tag2.reactive = Boolean(items[1]?.text && !items[1]?.error);

        if (items.length >= 2) {
            let tags = items.map(it => it.tag).join(' · ');
            this.pill.set_text(src + ' → ' + tags);

            this.tag1.set_label(items[0].tag);
            this.tag1.visible = true;
            this.trans1.set_text(items[0].text || items[0].error || 'Tarjima olinmadi');

            this.tag2.set_label(items[1].tag);
            this.tag2.visible = true;
            this.trans2.set_text(items[1].text || items[1].error || 'Tarjima olinmadi');
            this.row2.visible = true;

            this._copiedText = items[0].tag + ': ' + items[0].text + '\n' + items[1].tag + ': ' + items[1].text;
        } else {
            this.pill.set_text(src + ' → ' + items[0].tag);
            this.tag1.set_label(items[0].tag);
            this.tag1.visible = true;
            this.trans1.set_text(items[0].text);
            this.row2.visible = false;
            this._copiedText = items[0].text;
        }

        this._copiedText = items.filter(item => item.text && !item.error)
            .map(item => item.tag + ': ' + item.text).join('\n');
        this.copyBtn.reactive = Boolean(this._copiedText);
        this._ready = true;
        this._positionWidget();
        this._startAutoClose(8000);
    }

    setError(err) {
        if (this._destroyed) return;
        this._clearDeadline();
        this.state = 'error';
        this._ready = true;
        this._copiedText = '';
        this.copyBtn.reactive = false;
        this.tag1.reactive = false;
        this.tag2.reactive = false;
        this.speak1.reactive = false;
        this.speak2.reactive = false;
        this.saveBtn.reactive = false;
        this.pill.set_text('NOTICE');
        this.tag1.visible = false;
        this.trans1.set_text(err || 'Failed to translate');
        this.row2.visible = false;
        this._positionWidget();
        this._startAutoClose(8000);
    }

    _showExample(index) {
        const item = this._items?.[index];
        if (this._destroyed || !item?.text || item.error) return;
        this._exampleRequest?.cancel();
        this._meaningRequest?.cancel();
        if (this._meaningTimer) GLib.source_remove(this._meaningTimer);
        this._meaningTimer = 0;
        this._meaningLoading = false;
        if (this.meaningLabel) this.meaningLabel.visible = false;
        if (this._exampleTimer) GLib.source_remove(this._exampleTimer);
        this._exampleTimer = 0;
        const request = new Gio.Cancellable();
        this._exampleRequest = request;
        this._activeExample = null;
        if (this.exampleSpeak) this.exampleSpeak.visible = false;
        this.exampleLabel.visible = true;
        this.tag1.set_label(this._items[0].tag + (index === 0 ? ' ·' : ''));
        if (this._items[1]) this.tag2.set_label(this._items[1].tag + (index === 1 ? ' ·' : ''));
        const finish = (text, cache = false) => {
            if (this._destroyed || request.is_cancelled() || this._exampleRequest !== request) return;
            if (this._exampleTimer) GLib.source_remove(this._exampleTimer);
            this._exampleTimer = 0;
            this._exampleLoading = false;
            this.exampleLabel.set_text(item.tag + ' — ' + text);
            if (cache) this._exampleCache.set(item.tag, text);
            if (cache && this._savedCurrent) this._saveWord(true);
            if (cache || this._exampleCache.has(item.tag)) {
                this._showMeaning?.(text, item.tag);
                this._activeExample = {tag: item.tag, text};
                if (this.exampleSpeak) {
                    this.exampleSpeak.visible = ['RU', 'EN'].includes(item.tag);
                    this.exampleSpeak.reactive = Array.from(text).length <= 200;
                }
            }
            this._startAutoClose(8000);
        };
        if (this._exampleCache.has(item.tag)) {
            finish(this._exampleCache.get(item.tag));
            return;
        }
        this._exampleLoading = true;
        this._startAutoClose(8000);
        this.exampleLabel.set_text(item.tag + ' — Misol yuklanmoqda…');
        this._exampleTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 15000, () => {
            this._exampleTimer = 0;
            finish('Misol olinmadi. Qayta bosib urinib ko‘ring.');
            request.cancel();
            return GLib.SOURCE_REMOVE;
        });
        const fromEnglish = () => {
            const lookup = english => {
                fetchDictionaryExample(englishLookup(english), 'EN', (example, failed) => {
                    if (!example) {
                        finish(failed ? 'Internet aloqasini tekshirib, qayta urinib ko‘ring.' :
                            'Bu so‘z yoki ibora uchun misol topilmadi.');
                        return;
                    }
                    if (item.tag === 'EN') { finish(example, true); return; }
                    fetchOne(example, 'en', item.tag.toLowerCase(), (translated, _src, error) => {
                        finish(error ? 'Misol tarjima qilinmadi. Qayta urinib ko‘ring.' : translated, !error);
                    }, request);
                }, request);
            };
            const english = this._items.find(value => value.tag === 'EN' && value.text && !value.error);
            if (english) lookup(english.text);
            else fetchOne(item.text, item.tag.toLowerCase(), 'en', (text, _src, error) => {
                if (error) finish('Misol olinmadi. Qayta urinib ko‘ring.');
                else lookup(text);
            }, request);
        };
        fetchDictionaryExample(item.text, item.tag, (example, failed) => {
            if (example) finish(example, true);
            else if (failed) finish('Internet aloqasini tekshirib, qayta urinib ko‘ring.');
            else fromEnglish();
        }, request);
    }


    _showMeaning(text, tag) {
        if (!this.meaningLabel || this._destroyed) return;
        this._meaningCache ??= new Map();
        const key = tag + ':' + text;
        const request = new Gio.Cancellable();
        this._meaningRequest = request;
        this.meaningLabel.visible = true;
        const finish = (translation, error) => {
            if (this._destroyed || request.is_cancelled() || this._meaningRequest !== request) return;
            if (this._meaningTimer) GLib.source_remove(this._meaningTimer);
            this._meaningTimer = 0;
            this._meaningLoading = false;
            this.meaningLabel.set_text(error ? 'O‘zbekcha tarjima olinmadi. Tilni qayta bosing.' : translation);
            if (!error) {
                this._meaningCache.set(key, translation);
                if (this._savedCurrent) this._saveWord(true);
            }
            this._startAutoClose(8000);
        };
        if (tag === 'UZ') { finish(text, null); return; }
        if (this._meaningCache.has(key)) { finish(this._meaningCache.get(key), null); return; }
        this._meaningLoading = true;
        this.meaningLabel.set_text('O‘zbekcha ma’nosi yuklanmoqda…');
        this._startAutoClose(8000);
        this._meaningTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 12000, () => {
            this._meaningTimer = 0;
            finish('', true);
            request.cancel();
            return GLib.SOURCE_REMOVE;
        });
        fetchOne(text, tag.toLowerCase(), 'uz',
            (translation, _source, error) => finish(translation, error), request);
    }

    _textButton(label, callback) {
        const button = new St.Button({label, reactive: true, can_focus: true,
            style: 'color: #ececec; background-color: #242424; border-radius: 7px; padding: 5px 9px; margin-right: 5px; font-size: 12px;'});
        button.connect('clicked', callback);
        return button;
    }

    _iconButton(icon, description, callback) {
        const button = new St.Button({reactive: true, can_focus: true,
            accessible_name: description, y_align: Clutter.ActorAlign.START,
            style: 'color: #b4b4b4; padding: 5px; border-radius: 7px;'});
        button.set_child(new St.Icon({icon_name: icon, icon_size: 16}));
        button.connect('clicked', callback);
        return button;
    }

    _status(text) {
        if (this._destroyed) return;
        this._statusLabel.set_text(text);
        this._statusLabel.visible = Boolean(text);
    }

    _speak(item) {
        if (this._destroyed || !item?.text || item.error) return;
        if (this._voice.process && this._speakingText === item.text) {
            this._voice.stop();
            this._speechPlaying = false;
            this._status('');
            this._startAutoClose(8000);
            return;
        }
        this._speakingText = item.text;
        this._speechPlaying = true;
        this._startAutoClose(8000);
        this._status('O‘qilmoqda… Qayta bosish — to‘xtatish.');
        this._voice.play(item.text, item.tag, error => {
            this._speechPlaying = false;
            this._status(error);
            this._startAutoClose(8000);
        });
    }


    _saveWord(quiet = false) {
        if (!this._items?.length || this._items.some(item => !item.text || item.error)) return;
        try {
            this._store.save({
                original: this.originalText, src: this._resultSource,
                items: this._items.map(item => ({tag: item.tag, text: item.text})),
                examples: Object.fromEntries(this._exampleCache || []),
                meanings: Object.fromEntries(this._meaningCache || []),
            });
            this.saveBtn.set_label('Saqlandi');
            this._savedCurrent = true;
            if (!quiet) this._status('So‘z va ochilgan misollar lug‘atga saqlandi.');
        } catch (error) { this._status(error.message || 'Saqlab bo‘lmadi.'); }
    }

    _toggleLibrary() {
        const opening = !this._libraryScroll.visible;
        this._libraryScroll.visible = opening;
        this._mainScroll.visible = !opening;
        this.libraryBtn.set_label(opening ? 'Orqaga' : 'Lug‘at');
        this.saveBtn.visible = !opening;
        this.copyBtn.visible = !opening;
        this._status('');
        if (opening) this._renderLibrary();
        this._startAutoClose(8000);
    }

    _libraryLabel(text) {
        const label = new St.Label({text, x_expand: true,
            style: 'font-size: 14px; color: #ececec; margin-bottom: 10px;'});
        label.clutter_text.line_wrap = true;
        label.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        this._libraryBody.add_child(label);
        return label;
    }

    _renderLibrary(page = 0) {
        this._libraryBody.destroy_all_children();
        let entries;
        try { entries = this._store.list(); }
        catch (error) { this._libraryLabel('Lug‘at ochilmadi. Asl fayl o‘zgartirilmadi.'); return; }
        if (!entries.length) {
            this._libraryLabel('Hali saqlangan so‘z yo‘q. Tarjimadan keyin “Saqlash”ni bosing.');
            return;
        }
        const offset = page * 20;
        this._libraryLabel('Saqlangan so‘zlar · ' + entries.length);
        entries.slice(offset, offset + 20).forEach(entry => {
            const title = entry.original.replace(/\s+/g, ' ');
            const button = this._textButton(title.length > 44 ? title.slice(0, 41) + '…' : title,
                () => this._reviewSaved(entry, page));
            this._libraryBody.add_child(button);
        });
        const navigation = new St.BoxLayout();
        if (page > 0) navigation.add_child(this._textButton('Oldingi', () => this._renderLibrary(page - 1)));
        if (offset + 20 < entries.length)
            navigation.add_child(this._textButton('Keyingi', () => this._renderLibrary(page + 1)));
        this._libraryBody.add_child(navigation);
    }

    _reviewSaved(entry, page) {
        this._libraryBody.destroy_all_children();
        this._libraryLabel(entry.original);
        const answer = this._libraryLabel(entry.items.map(item => item.tag + ': ' + item.text +
            (entry.examples?.[item.tag] ? '\n' + entry.examples[item.tag] : '') +
            (entry.meanings?.[item.tag + ':' + entry.examples?.[item.tag]] ?
                '\n' + entry.meanings[item.tag + ':' + entry.examples[item.tag]] : '')).join('\n\n'));
        answer.visible = false;
        const reveal = this._textButton('Tarjimasini eslang · Javob', () => {
            answer.visible = !answer.visible;
            reveal.set_label(answer.visible ? 'Javobni yashirish' : 'Javob');
        });
        this._libraryBody.add_child(reveal);
        for (const item of entry.items.filter(item => ['RU', 'EN'].includes(item.tag)))
            this._libraryBody.add_child(this._textButton(item.tag + ' · Tinglash', () => this._speak(item)));
        this._libraryBody.add_child(this._textButton('Ro‘yxatga', () => this._renderLibrary(page)));
        let confirmed = false;
        const remove = this._textButton('O‘chirish', () => {
            if (!confirmed) { confirmed = true; remove.set_label('O‘chirishni tasdiqlash'); return; }
            try { this._store.remove(entry.id); this._renderLibrary(0); }
            catch (error) { this._status('O‘chirib bo‘lmadi.'); }
        });
        this._libraryBody.add_child(remove);
    }

    _copy() {
        if (!this._copiedText) return;
        St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, this._copiedText);
        this.copyBtn.set_label('Copied');
        if (this._copyTimer) GLib.source_remove(this._copyTimer);
        this._copyTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1500, () => {
            this._copyTimer = 0;
            if (!this._destroyed) this.copyBtn.set_label('Copy');
            return GLib.SOURCE_REMOVE;
        });
    }

    _setupEvents() {
        // Bolalar orasidagi enter/leave hodisalari taymerni buzmasin.
        this.actor.connect('notify::hover', () => {
            this._startAutoClose(8000);
        });

        // Faqat tezkor tugma shu qatlamda ishlanadi; Esc/tashqi bosish GrabHelperda.
        this._stageClickId = this._overlay.connect('captured-event', (_actor, event) => {
            if (event.type() !== Clutter.EventType.KEY_PRESS) return Clutter.EVENT_PROPAGATE;
            const symbol = event.get_key_symbol();
            const state = event.get_state();
            const ctrlAlt = Clutter.ModifierType.CONTROL_MASK | Clutter.ModifierType.MOD1_MASK;
            const forbidden = Clutter.ModifierType.SHIFT_MASK | Clutter.ModifierType.SUPER_MASK;
            if ((symbol === Clutter.KEY_z || symbol === Clutter.KEY_Z) &&
                (state & ctrlAlt) === ctrlAlt && !(state & forbidden)) {
                this.destroy();
                return Clutter.EVENT_STOP;
            }
            return Clutter.EVENT_PROPAGATE;
        });
        Main.overview.connectObject('showing', () => this.destroy(true), this);
        Main.sessionMode.connectObject('updated', () => this.destroy(true), this);
        Main.layoutManager.connectObject('monitors-changed', () => this.destroy(true), this);
    }

    _clearDeadline() {
        if (this._deadlineId) {
            GLib.source_remove(this._deadlineId);
            this._deadlineId = 0;
        }
    }

    startRequest(request) {
        if (this._destroyed) {
            request.cancel();
            return false;
        }
        this._cancellable = request;
        // Soup timeoutiga qo'shimcha butun tarjima oqimining qat'iy chegarasi.
        this._deadlineId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 20000, () => {
            this._deadlineId = 0;
            request.cancel();
            this.setError('Kutish vaqti tugadi. Oynani yopib, qayta urinib ko‘ring.');
            return GLib.SOURCE_REMOVE;
        });
        return true;
    }

    _startAutoClose(ms) {
        if (this._timerId) {
            GLib.source_remove(this._timerId);
            this._timerId = null;
        }
        if (this._destroyed || !this._ready || this._exampleLoading || this._meaningLoading ||
            this._speechPlaying || this.actor.hover) return;
        this._timerId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, ms, () => {
            this._timerId = null;
            this.destroy();
            return GLib.SOURCE_REMOVE;
        });
    }

    destroy(immediate = false) {
        // A network response can arrive after the user has closed the card.
        // Mark it first, so the extension can discard that stale response.
        if (this._destroyed) return;
        this._destroyed = true;
        this.state = 'closed';
        this._meaningRequest?.cancel();
        if (this._meaningTimer) {
            GLib.source_remove(this._meaningTimer);
            this._meaningTimer = 0;
        }
        this._voice?.stop();
        this._exampleRequest?.cancel();
        if (this._exampleTimer) {
            GLib.source_remove(this._exampleTimer);
            this._exampleTimer = 0;
        }
        this._clearDeadline();
        Main.overview.disconnectObject(this);
        Main.sessionMode.disconnectObject(this);
        Main.layoutManager.disconnectObject(this);
        this._grabHelper?.ungrab({actor: this.actor});
        this._cancellable?.cancel();
        if (this._copyTimer) {
            GLib.source_remove(this._copyTimer);
            this._copyTimer = 0;
        }

        if (this._timerId) {
            GLib.source_remove(this._timerId);
            this._timerId = null;
        }
        if (this._stageClickId) {
            this._overlay.disconnect(this._stageClickId);
            this._stageClickId = null;
        }
        if (this._stageKeyId) {
            global.stage.disconnect(this._stageKeyId);
            this._stageKeyId = null;
        }
        if (this.actor) {
            // Yopilish animatsiyasini kutmasdan input qatlamini bo'shatamiz.
            this._overlay.reactive = false;
            this.actor.reactive = false;
            this.actor.remove_all_transitions();
            if (immediate) {
                Main.layoutManager.removeChrome(this._overlay);
                this._overlay.destroy();
                this._overlay = null;
                this.actor = null;
                return;
            }
            this.actor.ease({
                opacity: 0,
                duration: 100,
                mode: Clutter.AnimationMode.EASE_OUT_QUAD,
                onComplete: () => {
                    if (this.actor) {
                        Main.layoutManager.removeChrome(this._overlay);
                        this._overlay.destroy();
                        this._overlay = null;
                        this.actor = null;
                    }
                }
            });
        }
    }
}
