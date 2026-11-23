/**
 * OCR xizmati (Query qatlami — ma'lumot qaytaradi, UI'ga tegmaydi).
 *
 * Ikki vazifa:
 *   1. Qotirilgan kadrni PNG faylga yozish (`composite_to_stream`);
 *   2. Tesseract'ni TSV rejimida chaqirib, har bir so'zning matni va
 *      aniq piksel koordinatasini qaytarish.
 *
 * TSV aynan shu maqsad uchun tanlandi: Live Text uslubidagi belgilash
 * uchun har bir so'zning to'rtburchagi kerak, vision modellar esa matnni
 * yaxshi o'qisa-da koordinatani ishonchli bermaydi.
 */

import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Shell from 'gi://Shell';

import {parseTsv} from './tsv-parser.js';

/** Tesseract juda sekin bo'lsa ham cheksiz kutmaymiz (ms). */
const OCR_TIMEOUT_MS = 15000;

/**
 * Qotirilgan stage teksturasini PNG faylga yozadi.
 *
 * Muhim: rasm aynan ekranda qotib turgan kadrdan olinadi, qayta
 * suratga olinmaydi — aks holda video siljib ketib, so'z koordinatalari
 * ekranda ko'rinayotgan tasvirga mos kelmay qolar edi.
 *
 * @param {Clutter.Content} content  screenshot_stage_to_content natijasi
 * @param {number} scale             shu content'ning masshtabi
 * @param {number} width             stage kengligi (mantiqiy piksel)
 * @param {number} height            stage balandligi (mantiqiy piksel)
 * @param {(path: string|null, error: string|null) => void} callback
 */
export function captureFrozenFrame(content, scale, width, height, callback) {
    let texture;
    try {
        texture = content.get_texture();
    } catch (e) {
        callback(null, `Qotirilgan kadr teksturasi olinmadi: ${e.message}`);
        return;
    }

    const path = GLib.build_filenamev([
        GLib.get_user_runtime_dir(),
        `quick-translate-ocr-${GLib.get_monotonic_time()}.png`,
    ]);

    let stream;
    try {
        const file = Gio.File.new_for_path(path);
        stream = file.replace(null, false, Gio.FileCreateFlags.PRIVATE, null);
    } catch (e) {
        callback(null, `Vaqtinchalik fayl yaratilmadi: ${e.message}`);
        return;
    }

    // Kursor teksturasi berilmaydi (null): sichqoncha ko'rsatkichi OCR'ni chalg'itmasin.
    Shell.Screenshot.composite_to_stream(
        texture,
        0, 0, width, height, scale,
        null, 0, 0, 1,
        stream,
        (obj, res) => {
            try {
                Shell.Screenshot.composite_to_stream_finish(res);
                stream.close(null);
                callback(path, null);
            } catch (e) {
                try {
                    stream.close(null);
                } catch (closeError) {
                    // Yopilmasa ham faylni o'chirishga harakat qilamiz.
                }
                deleteFrame(path);
                callback(null, `Kadr PNG'ga yozilmadi: ${e.message}`);
            }
        });
}

/**
 * Vaqtinchalik rasmni o'chiradi.
 *
 * Ekran tasvirida shaxsiy ma'lumot bo'lishi mumkin, shuning uchun OCR
 * tugashi bilan fayl darhol o'chiriladi — diskda qoldirilmaydi.
 */
export function deleteFrame(path) {
    if (!path)
        return;
    try {
        Gio.File.new_for_path(path).delete(null);
    } catch (e) {
        // Fayl allaqachon yo'q bo'lsa muammo emas.
    }
}

/** Tesseract o'rnatilganini tekshiradi. */
export function isTesseractAvailable() {
    return GLib.find_program_in_path('tesseract') !== null;
}

/**
 * PNG'dagi matnni so'zlarga ajratib o'qiydi.
 *
 * @param {string} path            PNG fayl yo'li
 * @param {string} languages       Tesseract tillari, masalan 'rus+eng'
 * @param {(words: Word[], error: string|null) => void} callback
 * @param {Gio.Cancellable} cancellable
 *
 * @typedef {object} Word
 * @property {string} text   so'zning o'zi
 * @property {number} conf   ishonch darajasi (0..100)
 * @property {number} x      chap chegara, piksel
 * @property {number} y      yuqori chegara, piksel
 * @property {number} w      kenglik, piksel
 * @property {number} h      balandlik, piksel
 * @property {number} line   satr raqami (o'qish tartibi uchun)
 * @property {number} index  o'qish tartibidagi o'rni
 */
export function recognizeWords(path, languages, callback, cancellable) {
    if (!isTesseractAvailable()) {
        callback([], "Tesseract o'rnatilmagan. Terminalda: sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng");
        return;
    }

    let proc;
    try {
        proc = Gio.Subprocess.new(
            ['tesseract', path, 'stdout', '-l', languages, '--psm', '3', 'tsv'],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
    } catch (e) {
        callback([], `Tesseract ishga tushmadi: ${e.message}`);
        return;
    }

    let timeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, OCR_TIMEOUT_MS, () => {
        timeoutId = 0;
        proc.force_exit();
        return GLib.SOURCE_REMOVE;
    });

    proc.communicate_utf8_async(null, cancellable, (p, res) => {
        if (timeoutId) {
            GLib.source_remove(timeoutId);
            timeoutId = 0;
        }

        let stdout = '';
        let stderr = '';
        try {
            const [, out, err] = p.communicate_utf8_finish(res);
            stdout = out || '';
            stderr = err || '';
        } catch (e) {
            if (!cancellable.is_cancelled())
                callback([], `Tesseract javobi o'qilmadi: ${e.message}`);
            return;
        }

        if (cancellable.is_cancelled())
            return;

        if (!p.get_successful()) {
            const hint = stderr.includes('Failed loading language')
                ? `Til fayli yo'q (${languages}). Kerakli tesseract-ocr-<til> paketini o'rnatish kerak.`
                : stderr.trim().split('\n').pop() || 'sabab aytilmadi';
            callback([], `Tesseract xato qaytardi: ${hint}`);
            return;
        }

        callback(parseTsv(stdout), null);
    });
}
