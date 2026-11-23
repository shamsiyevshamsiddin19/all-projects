/**
 * Tesseract TSV tahlilchisi — sof funksiya (Pure Function).
 *
 * Bu modul ataylab GNOME kutubxonalarini (gi://) import qilmaydi: shuning
 * uchun uni Shell'dan tashqarida, oddiy Node bilan ham sinash mumkin.
 * Kirish bir xil bo'lsa chiqish ham doim bir xil — hech qanday yon ta'sir yo'q.
 */

/** TSV'dagi level ustuni: 5 — so'z darajasi. */
const LEVEL_WORD = 5;

/** Bundan past ishonchli so'zlar tashlanadi (video fonida shovqin ko'p). */
export const MIN_CONFIDENCE = 40;

/**
 * Tesseract TSV natijasini so'zlar ro'yxatiga aylantiradi.
 *
 * Ustunlar tartibi: level page block par line word left top width height conf text
 * Tesseract so'zlarni o'qish tartibida beradi, shuning uchun massivdagi
 * o'rin (`index`) belgilashda tabiiy tartib sifatida ishlatiladi.
 *
 * @param {string} tsv                Tesseract'ning `tsv` chiqishi
 * @param {number} [minConfidence]    ishonch chegarasi
 * @returns {object[]} so'zlar: {text, conf, x, y, w, h, line, index}
 */
export function parseTsv(tsv, minConfidence = MIN_CONFIDENCE) {
    const words = [];
    const lineKeyToNumber = new Map();
    const rows = String(tsv ?? '').split('\n');

    for (let i = 1; i < rows.length; i++) { // 0-qator — sarlavha
        const cols = rows[i].split('\t');
        if (cols.length < 12)
            continue;

        if (parseInt(cols[0], 10) !== LEVEL_WORD)
            continue;

        const conf = parseFloat(cols[10]);
        const text = cols.slice(11).join('\t').trim();
        if (!text || !Number.isFinite(conf) || conf < minConfidence)
            continue;

        const x = parseInt(cols[6], 10);
        const y = parseInt(cols[7], 10);
        const w = parseInt(cols[8], 10);
        const h = parseInt(cols[9], 10);
        if (![x, y, w, h].every(Number.isFinite) || w <= 0 || h <= 0)
            continue;

        // block+par+line birgalikda yagona satrni aniqlaydi.
        const lineKey = `${cols[2]}:${cols[3]}:${cols[4]}`;
        if (!lineKeyToNumber.has(lineKey))
            lineKeyToNumber.set(lineKey, lineKeyToNumber.size);

        words.push({
            text,
            conf,
            x, y, w, h,
            line: lineKeyToNumber.get(lineKey),
            index: words.length,
        });
    }

    return words;
}

/**
 * Belgilangan so'zlardan matn yig'adi: bir satr ichi bo'sh joy bilan,
 * satrlar orasi yangi qator bilan. `text-layer.js` ham shu qoidadan
 * foydalanadi, shuning uchun mantiq shu yerda, bitta joyda turadi.
 *
 * @param {object[]} words  o'qish tartibidagi so'zlar
 * @returns {string}
 */
export function joinWords(words) {
    if (!words || words.length === 0)
        return '';

    let text = words[0].text;
    for (let i = 1; i < words.length; i++)
        text += words[i].line === words[i - 1].line ? ` ${words[i].text}` : `\n${words[i].text}`;
    return text;
}
