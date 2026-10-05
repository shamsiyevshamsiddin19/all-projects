package uz.shamsiyev.oyin.core

/**
 * Bitta ekran kadri — kulrang piksellar.
 * Android'dagi Bitmap ham, kompyuterdagi PNG ham shunga aylantiriladi,
 * shuning uchun tanish mantig'i ikkala joyda bir xil ishlaydi.
 */
class Frame(val width: Int, val height: Int, val gray: ByteArray) {
    init {
        require(gray.size == width * height) { "piksel soni o'lchamga mos emas" }
    }

    fun at(x: Int, y: Int): Int = gray[y * width + x].toInt() and 0xFF

    fun crop(r: PixelRect): Frame {
        val out = ByteArray(r.w * r.h)
        for (y in 0 until r.h) {
            System.arraycopy(gray, (r.y + y) * width + r.x, out, y * r.w, r.w)
        }
        return Frame(r.w, r.h, out)
    }

    /** Ikki kadr qanchalik farq qiladi (0.0 = bir xil). Ekran tinchlanganini bilish uchun. */
    fun diff(other: Frame, step: Int = 4): Double {
        require(other.width == width && other.height == height) { "kadr o'lchamlari har xil" }
        var sum = 0L
        var n = 0
        var i = 0
        while (i < gray.size) {
            sum += kotlin.math.abs((gray[i].toInt() and 0xFF) - (other.gray[i].toInt() and 0xFF))
            n++
            i += step
        }
        return if (n == 0) 0.0 else sum.toDouble() / n / 255.0
    }
}

/** Piksellardagi to'rtburchak. */
data class PixelRect(val x: Int, val y: Int, val w: Int, val h: Int)

/**
 * Nisbiy to'rtburchak — barcha qiymat 0..1 oralig'ida.
 * Shuning uchun bitta profil 720p da ham, 1080p da ham, planshetda ham ishlaydi.
 */
data class Roi(val x: Double, val y: Double, val w: Double, val h: Double) {
    fun toPixels(width: Int, height: Int) = PixelRect(
        (x * width).toInt().coerceIn(0, width - 1),
        (y * height).toInt().coerceIn(0, height - 1),
        (w * width).toInt().coerceAtLeast(1).coerceAtMost(width),
        (h * height).toInt().coerceAtLeast(1).coerceAtMost(height),
    )
}
