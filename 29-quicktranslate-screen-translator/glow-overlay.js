/**
 * Ekran chetidagi gradient halqa (Taqdimot qatlami).
 *
 * Vazifasi — foydalanuvchiga "qotirish rejimiga kirdingiz" degan aniq
 * vizual signal berish va rejim holatini rang bilan aytish:
 *   reading — sariq, tez puls   (matn o'qilmoqda)
 *   ready   — ko'k-siyoh, sokin (belgilashga tayyor)
 *   error   — qizil, pulssiz    (xato)
 *
 * ARZONLIK SHARTI (bu mashinada muhim — iGPU'ga 512 MB VRAM ajratilgan):
 *   - blur, soya, radial gradient va to'liq ekran qatlami ISHLATILMAYDI;
 *   - animatsiya faqat `opacity` ustida ketadi — kompozitor uchun eng arzon
 *     o'zgarish: qayta layout ham, qayta chizish ham talab qilmaydi;
 *   - jami 8 ta ingichka aktor (har chet uchun ikki rang qatlami).
 *
 * Gradient St'ning o'z imkoniyati bilan chiziladi: har bir chet chizig'i
 * chetdan ichkariga qarab shaffoflashadi, ikki rang qatlami esa teskari
 * fazada o'zaro so'nib-yonadi — natijada rang jimirlab turgandek ko'rinadi.
 *
 * MUHIM INVARIANT: bitta `opacity` xususiyatiga bir vaqtda faqat BITTA
 * animatsiya tegadi. Kirish `ease` (nomi 'opacity') va puls (nomi 'glow')
 * bir paytda ishlasa natija aniqlanmagan bo'ladi, shuning uchun puls faqat
 * kirish animatsiyasi tugagach boshlanadi va har safar oldin 'opacity'
 * transition'i olib tashlanadi.
 */

import Clutter from 'gi://Clutter';
import St from 'gi://St';

/** Halqa qalinligi (px). Sezilarli, lekin ekranni to'smaydigan o'lcham. */
const THICKNESS = 54;

/** Holatlar: [1-rang, 2-rang, puls davomiyligi ms (0 = pulssiz), eng past opacity]. */
const STATES = {
    reading: ['245, 165, 36', '245, 124, 36', 620, 70],
    ready: ['53, 132, 228', '145, 65, 172', 1500, 110],
    error: ['224, 27, 36', '224, 27, 36', 0, 255],
};

/** Kirish animatsiyasi (ms) — rejimga o'tilgani darhol sezilsin. */
const FADE_IN_MS = 180;

export class GlowOverlay {
    /**
     * @param {Clutter.Actor} parent  halqa qo'shiladigan konteyner
     * @param {number} width          ekran kengligi
     * @param {number} height         ekran balandligi
     */
    constructor(parent, width, height) {
        this._parent = parent;
        this._destroyed = false;
        this._entryDone = false;
        this._state = 'reading';

        // Har chet uchun: [geometriya, gradient yo'nalishi, chetdan ichkariga?]
        const edges = [
            [{x: 0, y: 0, width, height: THICKNESS}, 'vertical', true],
            [{x: 0, y: height - THICKNESS, width, height: THICKNESS}, 'vertical', false],
            [{x: 0, y: 0, width: THICKNESS, height}, 'horizontal', true],
            [{x: width - THICKNESS, y: 0, width: THICKNESS, height}, 'horizontal', false],
        ];

        /** Ikki rang qatlami: har biri 4 ta chet chizig'idan iborat. */
        this._layers = [[], []];
        for (const layer of [0, 1]) {
            for (const [geometry, direction, fromEdge] of edges) {
                const strip = new St.Widget({...geometry, reactive: false, opacity: 0});
                strip._direction = direction;
                strip._fromEdge = fromEdge;
                this._parent.add_child(strip);
                this._layers[layer].push(strip);
            }
        }

        this._applyColors();
        this._fadeIn();
    }

    /**
     * Halqani eng ustga ko'taradi. Konteynerga yangi bola qo'shilganda
     * chaqiriladi, aks holda matn qatlami halqani bosib qoladi.
     */
    raiseTop() {
        if (this._destroyed)
            return;
        for (const layer of this._layers) {
            for (const strip of layer)
                this._parent.set_child_above_sibling(strip, null);
        }
    }

    /**
     * Holatni — va shu bilan rang hamda puls tezligini — o'zgartiradi.
     * @param {'reading'|'ready'|'error'} state
     */
    setState(state) {
        if (this._destroyed || !STATES[state])
            return;

        this._state = state;
        this._applyColors();

        // Kirish animatsiyasi hali ketayotgan bo'lsa pulsni boshlamaymiz:
        // u tugagach `_fadeIn` o'zi joriy holat uchun pulsni yoqadi.
        if (this._entryDone)
            this._applyPulse();
    }

    /**
     * Halqani darhol yo'qotadi.
     *
     * So'nib chiqish animatsiyasi ataylab yo'q: overlay yopilganda butun
     * konteyner bir vaqtda yo'q qilinadi, shuning uchun bunday animatsiya
     * hech qachon ko'rinmaydi — faqat yolg'on murakkablik bo'lardi.
     */
    destroy() {
        if (this._destroyed)
            return;
        this._destroyed = true;

        for (const layer of this._layers) {
            for (const strip of layer) {
                strip.remove_transition('glow');
                strip.remove_transition('opacity');
                strip.destroy();
            }
        }
        this._layers = [[], []];
    }

    _applyColors() {
        const [colorA, colorB] = STATES[this._state];
        this._paint(this._layers[0], colorA);
        this._paint(this._layers[1], colorB);
    }

    _paint(strips, rgb) {
        for (const strip of strips) {
            const opaque = `rgba(${rgb}, 0.95)`;
            const clear = `rgba(${rgb}, 0)`;
            const [start, end] = strip._fromEdge ? [opaque, clear] : [clear, opaque];
            strip.set_style(
                `background-gradient-direction: ${strip._direction}; ` +
                `background-gradient-start: ${start}; ` +
                `background-gradient-end: ${end};`);
        }
    }

    /** Birinchi qatlamni 0 dan to'liq ko'rinishga olib chiqadi, keyin puls. */
    _fadeIn() {
        for (const strip of this._layers[0]) {
            strip.ease({
                opacity: 255,
                duration: FADE_IN_MS,
                mode: Clutter.AnimationMode.EASE_OUT_QUAD,
            });
        }
        // Ikkinchi qatlam kirishda ko'rinmaydi — u pulsda qo'shiladi.
        for (const strip of this._layers[1])
            strip.opacity = 0;

        const first = this._layers[0][0];
        if (!first) {
            this._entryDone = true;
            return;
        }
        const entry = first.get_transition('opacity');
        if (!entry) {
            this._entryDone = true;
            this._applyPulse();
            return;
        }
        entry.connect('stopped', () => {
            if (this._destroyed)
                return;
            this._entryDone = true;
            this._applyPulse();
        });
    }

    /**
     * Joriy holat uchun pulsni qo'yadi: ikki rang qatlami teskari fazada
     * o'zaro so'nib-yonadi.
     *
     * `auto_reverse` + cheksiz `repeat_count` ishlatiladi — animatsiyani
     * kompozitorning o'zi yuritadi, JS tomonda har kadrda hech narsa
     * hisoblanmaydi.
     */
    _applyPulse() {
        const [, , durationMs, minOpacity] = STATES[this._state];

        for (const layer of [0, 1]) {
            for (const strip of this._layers[layer]) {
                // Bitta xususiyatga ikki animatsiya tegmasligi uchun.
                strip.remove_transition('glow');
                strip.remove_transition('opacity');

                if (durationMs === 0) {
                    // Pulssiz holat (xato): faqat birinchi qatlam ko'rinadi.
                    strip.opacity = layer === 0 ? 255 : 0;
                    continue;
                }

                const transition = new Clutter.PropertyTransition({property_name: 'opacity'});
                // Ikkinchi qatlam teskari fazadan boshlanadi.
                transition.set_from(layer === 0 ? 255 : minOpacity);
                transition.set_to(layer === 0 ? minOpacity : 255);
                transition.set_duration(durationMs);
                transition.set_auto_reverse(true);
                transition.set_repeat_count(-1);
                transition.set_progress_mode(Clutter.AnimationMode.EASE_IN_OUT_SINE);
                strip.add_transition('glow', transition);
            }
        }
    }
}
