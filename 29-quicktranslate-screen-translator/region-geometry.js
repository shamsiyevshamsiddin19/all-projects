/**
 * Maydon geometriyasi — sof funksiyalar (Pure Functions).
 *
 * Bu modul ataylab GNOME kutubxonalarini (gi://) import qilmaydi, shuning
 * uchun uni Shell'dan tashqarida, oddiy Node bilan sinash mumkin.
 * Kirish bir xil bo'lsa chiqish ham doim bir xil — yon ta'sir yo'q.
 */

/**
 * Tasodifiy bosishni maydon deb hisoblamaslik uchun eng kichik o'lcham (px).
 * Bundan kichik tanlov e'tiborsiz qoldiriladi.
 */
export const MIN_REGION_SIZE = 12;

/**
 * Sudrashning boshi va oxiridan to'rtburchak yasaydi.
 *
 * Sudrash istalgan yo'nalishda bo'lishi mumkin — o'ngdan chapga, pastdan
 * yuqoriga — shuning uchun koordinatalar tartibga solinadi va kenglik
 * hamda balandlik hech qachon manfiy bo'lmaydi.
 *
 * @returns {{x: number, y: number, width: number, height: number}}
 */
export function normalizeRect(startX, startY, endX, endY) {
    const x = Math.min(startX, endX);
    const y = Math.min(startY, endY);
    return {
        x: Math.round(x),
        y: Math.round(y),
        width: Math.round(Math.abs(endX - startX)),
        height: Math.round(Math.abs(endY - startY)),
    };
}

/**
 * Maydonni ekran chegarasi ichiga qisadi.
 *
 * Sudrash ekran tashqarisiga chiqib ketishi mumkin; chegaradan tashqaridagi
 * koordinata bilan rasm kesishga urinish xatoga olib kelardi.
 *
 * @param {{x,y,width,height}} rect
 * @param {{width: number, height: number}} bounds
 */
export function clampRect(rect, bounds) {
    const x = Math.max(0, Math.min(rect.x, bounds.width));
    const y = Math.max(0, Math.min(rect.y, bounds.height));
    return {
        x,
        y,
        width: Math.max(0, Math.min(rect.width, bounds.width - x)),
        height: Math.max(0, Math.min(rect.height, bounds.height - y)),
    };
}

/** Maydon OCR uchun yetarlicha kattami. */
export function isUsableRegion(rect, minSize = MIN_REGION_SIZE) {
    return Boolean(rect) && rect.width >= minSize && rect.height >= minSize;
}
