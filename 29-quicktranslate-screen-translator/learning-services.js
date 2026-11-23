import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

// Faqat foydalanuvchi saqlagan yozuvlar. Buzilgan bazani ustidan yozmaymiz.
export class VocabularyStore {
    constructor(directory = GLib.build_filenamev([GLib.get_user_data_dir(), 'quick-translate'])) {
        this.directory = directory;
        this.file = Gio.File.new_for_path(GLib.build_filenamev([directory, 'vocabulary.json']));
    }

    list() {
        try {
            const [, bytes] = this.file.load_contents(null);
            const data = JSON.parse(new TextDecoder().decode(bytes));
            if (data.version !== 1 || !Array.isArray(data.entries) ||
                data.entries.some(entry => typeof entry.id !== 'string' ||
                    typeof entry.original !== 'string' || !Array.isArray(entry.items) ||
                    entry.items.some(item => typeof item.tag !== 'string' || typeof item.text !== 'string')))
                throw new Error('Saqlangan so‘zlar fayli noto‘g‘ri. Asl fayl saqlandi.');
            return data.entries;
        } catch (error) {
            if (error.matches?.(Gio.io_error_quark(), Gio.IOErrorEnum.NOT_FOUND)) return [];
            throw error;
        }
    }

    save(record) {
        const entries = this.list();
        const id = JSON.stringify([record.src, record.original.trim().toLocaleLowerCase()]);
        const index = entries.findIndex(entry => entry.id === id);
        const entry = {...record, id, savedAt: new Date().toISOString()};
        if (index >= 0) entries[index] = entry;
        else {
            if (entries.length >= 500) throw new Error('Lug‘atda 500 ta yozuv bor. Avval keraksizini o‘chiring.');
            entries.unshift(entry);
        }
        this._write(entries);
        return id;
    }

    remove(id) {
        this._write(this.list().filter(entry => entry.id !== id));
    }

    _write(entries) {
        if (GLib.mkdir_with_parents(this.directory, 0o700) !== 0)
            throw new Error('Lug‘at papkasini yaratib bo‘lmadi.');
        this.file.replace_contents(JSON.stringify({version: 1, entries}, null, 2),
            null, true, Gio.FileCreateFlags.PRIVATE | Gio.FileCreateFlags.REPLACE_DESTINATION, null);
    }
}

// Tashqi jarayon argv bilan chaqiriladi: matn shell kodi sifatida bajarilmaydi.
export class Pronunciation {
    stop() {
        if (this.timer) GLib.source_remove(this.timer);
        this.timer = 0;
        const process = this.process;
        this.process = null;
        if (process) {
            try { process.force_exit(); } catch (_error) {}
        }
    }

    play(text, language, done) {
        this.stop();
        if (!['EN', 'RU'].includes(language)) {
            done('Hozircha ovoz EN va RU uchun mavjud.');
            return;
        }
        if (!text || Array.from(text).length > 200) {
            done('O‘qish uchun 200 belgigacha bo‘lgan so‘z yoki gapni tanlang.');
            return;
        }
        const player = GLib.find_program_in_path('ffplay');
        if (!player) { done('Ovoz uchun ffplay o‘rnatilishi kerak.'); return; }
        const url = 'https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=' +
            language.toLowerCase() + '&q=' + encodeURIComponent(text);
        let process;
        try {
            process = Gio.Subprocess.new([player, '-nodisp', '-autoexit', '-loglevel', 'quiet',
                '-nostats', '-rw_timeout', '10000000', url],
            Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE);
        } catch (_error) { done('Ovozni ishga tushirib bo‘lmadi.'); return; }
        this.process = process;
        this.timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 30000, () => {
            this.timer = 0;
            this.stop();
            done('Ovoz uchun kutish vaqti tugadi.');
            return GLib.SOURCE_REMOVE;
        });
        process.wait_async(null, (child, result) => {
            let ok = false;
            try { child.wait_finish(result); ok = child.get_successful(); } catch (_error) {}
            if (this.process !== process) return;
            this.process = null;
            if (this.timer) GLib.source_remove(this.timer);
            this.timer = 0;
            done(ok ? '' : 'Ovoz olinmadi. Internet aloqasini tekshiring.');
        });
    }
}
