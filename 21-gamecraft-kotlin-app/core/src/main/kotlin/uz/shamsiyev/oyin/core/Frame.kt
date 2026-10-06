package uz.shamsiyev.oyin.core

/**
 * Bitta ekran kadri — har piksel 0xRRGGBB ko'rinishida.
 *
 * Android'dagi Bitmap ham, kompyuterdagi PNG ham shunga aylantiriladi,
 * shuning uchun tanish mantig'i ikkala joyda bir xil ishlaydi.
 * Rang kerak: qora/qizil mast, oq karta, sariq pufakcha, yashil halqa —
 * hammasi rang bilan ajraladi.
 */
class Frame(val width: Int, val height: Int, val pixels: IntArray) {
    init {
        require(pixels.size == width * height) { "piksel soni o'lchamga mos emas" }
    }

    inline fun idx(x: Int, y: Int) = y * width + x
    inline fun r(i: Int) = (pixels[i] shr 16) and 0xFF
    inline fun g(i: Int) = (pixels[i] shr 8) and 0xFF
    inline fun b(i: Int) = pixels[i] and 0xFF

    /** PIL "L" bilan bir xil: 0.299R + 0.587G + 0.114B */
    fun gray(i: Int): Double = 0.299 * r(i) + 0.587 * g(i) + 0.114 * b(i)

    fun crop(rect: PixelRect): Frame {
        val out = IntArray(rect.w * rect.h)
        for (y in 0 until rect.h) {
            System.arraycopy(pixels, (rect.y + y) * width + rect.x, out, y * rect.w, rect.w)
        }
        return Frame(rect.w, rect.h, out)
    }

    /** Soat strelkasiga teskari 90 gradus burish — yonboshlagan kozir kartasi uchun. */
    fun rotate90(): Frame {
        val out = IntArray(pixels.size)
        for (y in 0 until height) {
            for (x in 0 until width) {
                // np.rot90(k=1) bilan bir xil: yangi[width-1-x][y] = eski[y][x]
                out[(width - 1 - x) * height + y] = pixels[y * width + x]
            }
        }
        return Frame(height, width, out)
    }

    /** Ikki kadr qanchalik farq qiladi (0.0 = bir xil). Ekran tinchlanganini bilish uchun. */
    fun diff(other: Frame, step: Int = 7): Double {
        require(other.width == width && other.height == height) { "kadr o'lchamlari har xil" }
        var sum = 0L
        var n = 0
        var i = 0
        while (i < pixels.size) {
            sum += Math.abs(r(i) - other.r(i)) + Math.abs(g(i) - other.g(i)) + Math.abs(b(i) - other.b(i))
            n++
            i += step
        }
        return if (n == 0) 0.0 else sum.toDouble() / n / (3 * 255.0)
    }
}

/** Piksellardagi to'rtburchak. */
data class PixelRect(val x: Int, val y: Int, val w: Int, val h: Int) {
    val right get() = x + w
    val bottom get() = y + h
    val cx get() = x + w / 2.0
    val cy get() = y + h / 2.0
}

/**
 * Nisbiy to'rtburchak — barcha qiymat 0..1 oralig'ida.
 * Shuning uchun bitta profil 720p da ham, 1080p da ham ishlaydi.
 */
data class Roi(val x: Double, val y: Double, val w: Double, val h: Double) {
    fun toPixels(width: Int, height: Int): PixelRect {
        val px = (x * width).toInt().coerceIn(0, width - 1)
        val py = (y * height).toInt().coerceIn(0, height - 1)
        val pw = (w * width).toInt().coerceIn(1, width - px)
        val ph = (h * height).toInt().coerceIn(1, height - py)
        return PixelRect(px, py, pw, ph)
    }

    fun ichidami(cx: Double, cy: Double, width: Int, height: Int): Boolean {
        val p = toPixels(width, height)
        return cx >= p.x && cx <= p.right && cy >= p.y && cy <= p.bottom
    }
}
