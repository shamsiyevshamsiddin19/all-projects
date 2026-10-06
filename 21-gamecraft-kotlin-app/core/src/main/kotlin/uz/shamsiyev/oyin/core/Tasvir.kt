package uz.shamsiyev.oyin.core

import java.io.DataInputStream
import java.io.InputStream

/** Mantiqiy maska — har piksel uchun ha/yo'q. */
class Maska(val width: Int, val height: Int, val bits: BooleanArray) {
    inline operator fun get(i: Int) = bits[i]
    fun soni(): Int {
        var n = 0
        for (b in bits) if (b) n++
        return n
    }

    infix fun va(other: Maska): Maska {
        val out = BooleanArray(bits.size)
        for (i in bits.indices) out[i] = bits[i] && other.bits[i]
        return Maska(width, height, out)
    }

    /**
     * Manhattan masofasi bo'yicha kengaytirish — scipy'dagi
     * `binary_dilation(iterations = n)` bilan bir xil natija beradi
     * (ikkalasi ham krest shaklidagi element bilan ishlaydi).
     * Ikki o'tishli masofa hisobi bilan: n marta takrorlashdan ancha tez.
     */
    fun kengaytir(n: Int): Maska {
        if (n <= 0) return this
        val katta = width * height + 1
        val d = IntArray(bits.size) { if (bits[it]) 0 else katta }
        for (y in 0 until height) {
            for (x in 0 until width) {
                val i = y * width + x
                if (x > 0) d[i] = minOf(d[i], d[i - 1] + 1)
                if (y > 0) d[i] = minOf(d[i], d[i - width] + 1)
            }
        }
        for (y in height - 1 downTo 0) {
            for (x in width - 1 downTo 0) {
                val i = y * width + x
                if (x < width - 1) d[i] = minOf(d[i], d[i + 1] + 1)
                if (y < height - 1) d[i] = minOf(d[i], d[i + width] + 1)
            }
        }
        return Maska(width, height, BooleanArray(bits.size) { d[it] <= n })
    }
}

/** Bog'langan bo'lak: chegaraviy to'rtburchak va piksellar soni. */
data class Bolak(val x: Int, val y: Int, val w: Int, val h: Int, val maydon: Int) {
    val right get() = x + w
    val bottom get() = y + h
    val cx get() = x + w / 2.0
    val cy get() = y + h / 2.0
    fun rect() = PixelRect(x, y, w, h)
}

/**
 * Bog'langan bo'laklarni topadi (4 tomonlama qo'shnilik — scipy'ning
 * standart holati bilan bir xil). Ikki o'tish + birlashtirish daraxti.
 */
fun bolaklar(m: Maska, minMaydon: Int = 1, maxMaydon: Int = Int.MAX_VALUE): List<Bolak> {
    val n = m.bits.size
    val teg = IntArray(n)
    // Birlashtirish daraxti oddiy IntArray da: ArrayList<Int> da har murojaat
    // sonni o'ramga o'rab, telefonda sezilarli sekinlashtiradi.
    var ota = IntArray(1024)
    var tegSoni = 1

    fun yangiTeg(): Int {
        if (tegSoni >= ota.size) ota = ota.copyOf(ota.size * 2)
        ota[tegSoni] = tegSoni
        return tegSoni++
    }

    fun ildiz(a: Int): Int {
        var r = a
        while (ota[r] != r) r = ota[r]
        var c = a
        while (ota[c] != c) { val k = ota[c]; ota[c] = r; c = k }
        return r
    }

    for (y in 0 until m.height) {
        val qator = y * m.width
        for (x in 0 until m.width) {
            val i = qator + x
            if (!m.bits[i]) continue
            val chap = if (x > 0 && m.bits[i - 1]) teg[i - 1] else 0
            val tepa = if (y > 0 && m.bits[i - m.width]) teg[i - m.width] else 0
            teg[i] = when {
                chap != 0 && tepa != 0 -> {
                    val ra = ildiz(chap); val rb = ildiz(tepa)
                    val kichik = minOf(ra, rb)
                    if (ra != rb) ota[maxOf(ra, rb)] = kichik
                    kichik
                }
                chap != 0 -> chap
                tepa != 0 -> tepa
                else -> yangiTeg()
            }
        }
    }

    // Har teg uchun chegaraviy to'rtburchak
    val x0 = IntArray(tegSoni) { Int.MAX_VALUE }
    val y0 = IntArray(tegSoni) { Int.MAX_VALUE }
    val x1 = IntArray(tegSoni) { -1 }
    val y1 = IntArray(tegSoni) { -1 }
    val maydon = IntArray(tegSoni)
    for (y in 0 until m.height) {
        val qator = y * m.width
        for (x in 0 until m.width) {
            val t = teg[qator + x]
            if (t == 0) continue
            val r = ildiz(t)
            if (x < x0[r]) x0[r] = x
            if (y < y0[r]) y0[r] = y
            if (x > x1[r]) x1[r] = x
            if (y > y1[r]) y1[r] = y
            maydon[r]++
        }
    }

    val out = ArrayList<Bolak>()
    for (t in 1 until tegSoni) {
        if (x1[t] < 0 || maydon[t] < minMaydon || maydon[t] > maxMaydon) continue
        out.add(Bolak(x0[t], y0[t], x1[t] - x0[t] + 1, y1[t] - y0[t] + 1, maydon[t]))
    }
    out.sortBy { it.x }
    return out
}

/** Namuna o'lchami — Python tarafdagi bilan bir xil bo'lishi shart. */
const val NAMUNA_OLCHAMI = 40

/**
 * Belgini kesib, kvadratga to'ldirib, bir xil o'lchamga keltiradi va
 * yorug'likdan mustaqil qiladi (o'rtachasi ayiriladi, uzunligi 1 ga keltiriladi).
 *
 * Kvadratga to'ldirish nisbatni saqlaydi — "1" bilan "0" shu bilan farqlanadi.
 */
fun namuna(frame: Frame, quti: PixelRect, chet: Int = 2): FloatArray? {
    val x0 = (quti.x - chet).coerceAtLeast(0)
    val y0 = (quti.y - chet).coerceAtLeast(0)
    val x1 = (quti.right + chet).coerceAtMost(frame.width)
    val y1 = (quti.bottom + chet).coerceAtMost(frame.height)
    val w = x1 - x0
    val h = y1 - y0
    if (w <= 0 || h <= 0) return null

    val tomon = maxOf(w, h)
    val kvadrat = DoubleArray(tomon * tomon) { 255.0 }
    val ox = (tomon - w) / 2
    val oy = (tomon - h) / 2
    for (y in 0 until h) {
        for (x in 0 until w) {
            kvadrat[(oy + y) * tomon + ox + x] = frame.gray(frame.idx(x0 + x, y0 + y))
        }
    }

    val kichik = kichiklashtir(kvadrat, tomon, NAMUNA_OLCHAMI)
    var ortacha = 0.0
    for (v in kichik) ortacha += v
    ortacha /= kichik.size
    var uzunlik = 0.0
    for (i in kichik.indices) {
        kichik[i] -= ortacha
        uzunlik += kichik[i] * kichik[i]
    }
    uzunlik = Math.sqrt(uzunlik)
    if (uzunlik < 1e-6) return null
    return FloatArray(kichik.size) { (kichik[it] / uzunlik).toFloat() }
}

/** Maydon bo'yicha o'rtachalash — kattadan kichikka keltirishning barqaror usuli. */
private fun kichiklashtir(manba: DoubleArray, tomon: Int, yangi: Int): DoubleArray {
    val out = DoubleArray(yangi * yangi)
    val nisbat = tomon.toDouble() / yangi
    for (y in 0 until yangi) {
        val sy0 = y * nisbat
        val sy1 = (y + 1) * nisbat
        for (x in 0 until yangi) {
            val sx0 = x * nisbat
            val sx1 = (x + 1) * nisbat
            var sum = 0.0
            var ogirlik = 0.0
            var yy = Math.floor(sy0).toInt()
            while (yy < sy1 && yy < tomon) {
                val hy = minOf(sy1, (yy + 1).toDouble()) - maxOf(sy0, yy.toDouble())
                var xx = Math.floor(sx0).toInt()
                while (xx < sx1 && xx < tomon) {
                    val hx = minOf(sx1, (xx + 1).toDouble()) - maxOf(sx0, xx.toDouble())
                    val w = hy * hx
                    sum += manba[yy * tomon + xx] * w
                    ogirlik += w
                    xx++
                }
                yy++
            }
            out[y * yangi + x] = if (ogirlik > 0) sum / ogirlik else 255.0
        }
    }
    return out
}

/** Tanish natijasi: nom, o'xshashlik va ikkinchi o'rindagi boshqa nomdan farq. */
data class Topildi(val nom: String?, val ball: Float, val farq: Float)

/**
 * Shablon banki: o'rgatilgan namunalar va ularning nomlari.
 *
 * Tanish — eng o'xshash shablonni topish. Mutlaq o'xshashlik yetarli mezon emas:
 * belgi kartadagi rasm bilan qisman yopishib qolsa ball tushadi, lekin baribir
 * to'g'ri javobdan ancha oldinda turadi. Shuning uchun "qancha oldinda" ham hisoblanadi.
 */
class ShablonBanki(private val vektorlar: Array<FloatArray>, private val nomlar: List<String>) {

    fun tanla(v: FloatArray?, ruxsat: Set<String>? = null): Topildi {
        if (v == null) return Topildi(null, 0f, 0f)
        val eng = HashMap<String, Float>()
        for (i in vektorlar.indices) {
            val nom = nomlar[i]
            if (ruxsat != null && nom !in ruxsat) continue
            var s = 0f
            val t = vektorlar[i]
            for (k in v.indices) s += t[k] * v[k]
            val oldingi = eng[nom]
            if (oldingi == null || s > oldingi) eng[nom] = s
        }
        if (eng.isEmpty()) return Topildi(null, 0f, 0f)
        val tartib = eng.entries.sortedByDescending { it.value }
        val ikkinchi = if (tartib.size > 1) tartib[1].value else 0f
        return Topildi(tartib[0].key, tartib[0].value, tartib[0].value - ikkinchi)
    }

    companion object {
        /** Yuqori o'xshashlik, yoki pastroq bo'lsa ham raqobatchidan aniq oldinda. */
        fun qabul(t: Topildi, mutlaq: Float = 0.72f, past: Float = 0.50f, kerakliFarq: Float = 0.10f) =
            t.nom != null && (t.ball >= mutlaq || (t.ball >= past && t.farq >= kerakliFarq))

        fun oqi(bank: InputStream, nomlar: List<String>): ShablonBanki {
            DataInputStream(bank.buffered()).use { s ->
                val soni = java.lang.Integer.reverseBytes(s.readInt())
                val olcham = java.lang.Integer.reverseBytes(s.readInt())
                require(nomlar.size == soni) { "nomlar soni mos emas: ${nomlar.size} != $soni" }
                val out = Array(soni) { FloatArray(olcham) }
                for (i in 0 until soni) {
                    for (j in 0 until olcham) {
                        out[i][j] = java.lang.Float.intBitsToFloat(java.lang.Integer.reverseBytes(s.readInt()))
                    }
                }
                return ShablonBanki(out, nomlar)
            }
        }
    }
}
