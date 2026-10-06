package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.core.*

/**
 * Ekranni o'qish: kartalar, kozir, zaxira soni, hodisa pufakchalari, himoyachi.
 *
 * Asosiy g'oya: zona-zona sozlash o'rniga KARTA BURCHAGI qidiriladi —
 * toza oq fonda raqam, uning tagida mast. Shu naqsh qo'lda ham, stolda ham,
 * kozir kartada ham bir xil, shuning uchun bitta mantiq uchalasiga yetadi.
 */
object Koz {

    // --- hududlar (nisbiy, shuning uchun ekran o'lchamiga bog'liq emas) ---
    val KOZIR_ROI = Roi(0.0, 0.33, 0.22, 0.26)
    val ZAXIRA_ROI = Roi(0.0, 0.305, 0.095, 0.040)
    val AVATARLAR = listOf(
        "chap" to Roi(0.226, 0.086, 0.185, 0.083),
        "ong" to Roi(0.613, 0.086, 0.185, 0.083),
        "men" to Roi(0.417, 0.859, 0.185, 0.083),
    )
    private val PUFAK_JOYLARI = listOf(
        Triple("chap", 0.30, 0.105), Triple("ong", 0.70, 0.105), Triple("men", 0.50, 0.855),
    )
    private const val PUFAK_ENI = 0.30
    private const val PUFAK_BOYI = 0.075

    // --- rang maskalari ---
    private inline fun maska(f: Frame, shart: (Int, Int, Int) -> Boolean): Maska {
        val bits = BooleanArray(f.pixels.size)
        for (i in f.pixels.indices) bits[i] = shart(f.r(i), f.g(i), f.b(i))
        return Maska(f.width, f.height, bits)
    }

    fun oq(f: Frame) = maska(f) { r, g, b ->
        r > 170 && g > 170 && b > 170 && (maxOf(r, g, b) - minOf(r, g, b)) < 45
    }

    fun qora(f: Frame) = maska(f) { r, g, b -> maxOf(r, g, b) < 120 }

    fun qizil(f: Frame) = maska(f) { r, g, b -> r > 110 && r - maxOf(g, b) > 55 }

    private fun oqMatn(f: Frame) = maska(f) { r, g, b ->
        r > 190 && g > 190 && b > 190 && (maxOf(r, g, b) - minOf(r, g, b)) < 35
    }

    private fun oqPufak(f: Frame) = maska(f) { r, g, b ->
        r > 215 && g > 215 && b > 215 && (maxOf(r, g, b) - minOf(r, g, b)) < 25
    }

    private fun sariq(f: Frame) = maska(f) { r, g, b ->
        r > 180 && g > 150 && b < 120 && r - b > 80 && g - b > 60
    }

    // --- karta burchagi ---

    data class Burchak(val rang: String, val rank: Bolak, val suit: Bolak, val quti: Bolak, val oqlik: Double)

    /**
     * "10" ning ikki bo'lagini birlashtiradi.
     *
     * Shart qattiq: chapdagisi ingichka tayoq ('1'), o'ngdagisi shunga teng
     * balandlikda ('0') va oraliq juda kichik. Aks holda qo'shni KARTA belgisi
     * ham yopishib ketadi — bir paytlar aynan shunday bo'lgan.
     */
    private fun oninchiniBirlashtir(parts: List<Bolak>): List<Bolak> {
        val tartib = parts.sortedBy { it.x }
        val ishlatilgan = HashSet<Int>()
        val out = ArrayList<Bolak>(tartib.size)
        for (i in tartib.indices) {
            if (i in ishlatilgan) continue
            val p = tartib[i]
            var birlashdi = false
            for (j in i + 1 until tartib.size) {
                if (j in ishlatilgan) continue
                val q = tartib[j]
                val gap = q.x - p.right
                if (gap > 0.18 * p.h) break
                val ingichka = p.w <= 0.45 * p.h
                val birXil = q.h >= 0.8 * p.h && q.h <= 1.25 * p.h
                val yk = minOf(p.bottom, q.bottom) - maxOf(p.y, q.y)
                if (ingichka && birXil && gap >= -4 && yk > 0.7 * maxOf(p.h, q.h)) {
                    val x0 = minOf(p.x, q.x); val y0 = minOf(p.y, q.y)
                    out.add(Bolak(x0, y0, maxOf(p.right, q.right) - x0, maxOf(p.bottom, q.bottom) - y0,
                        p.maydon + q.maydon))
                    ishlatilgan.add(i); ishlatilgan.add(j)
                    birlashdi = true
                    break
                }
            }
            if (!birlashdi) out.add(p)
        }
        return out
    }

    /** Cho'qqidan keyingi birinchi botiq — belgi va unga yopishgan rasm orasidagi eng ingichka joy. */
    private fun botiq(profil: DoubleArray, minOrin: Int): Int? {
        if (profil.isEmpty()) return null
        var choqqi = 0
        for (i in profil.indices) if (profil[i] > profil[choqqi]) choqqi = i
        var i = choqqi
        while (i + 1 < profil.size && profil[i + 1] <= profil[i]) i++
        return if (i > minOrin && i + 1 < profil.size && profil[i] < 0.6 * profil[choqqi]) i + 1 else null
    }

    /**
     * Mast belgisi kartadagi rasm bilan yopishib ketgan bo'lsa, ortig'ini kesadi.
     * Yopishish ko'pincha pastdan bo'ladi: yurak qirolning qizil kiyimiga.
     */
    private fun mastKes(suit: Bolak, rank: Bolak, m: Maska): Bolak {
        val meYorH = 0.72 * rank.h
        val meYorW = 0.85 * rank.h
        if (suit.h <= meYorH && suit.w <= meYorW) return suit

        var h = suit.h
        var w = suit.w
        if (suit.h > meYorH) {
            val qator = DoubleArray(suit.h) { y ->
                var s = 0.0
                for (x in suit.x until suit.right) if (m.bits[(suit.y + y) * m.width + x]) s++
                s
            }
            botiq(qator, (0.25 * suit.h).toInt())?.let { h = it }
        }
        if (suit.w > meYorW) {
            val ustun = DoubleArray(suit.w) { x ->
                var s = 0.0
                for (y in suit.y until suit.y + h) if (m.bits[y * m.width + suit.x + x]) s++
                s
            }
            botiq(ustun, (0.25 * suit.w).toInt())?.let { w = it }
        }
        if (h < 0.25 * rank.h || w < 0.2 * rank.h) return suit
        return Bolak(suit.x, suit.y, w, h, suit.maydon)
    }

    /**
     * Burchak belgisi atrofi oq bo'lishi kerak. Kartaning o'rtasidagi rasm ichida
     * ham qora chiziqlar bor, lekin ular atrofi rang-barang; burchakdagi raqam esa
     * toza oq fonda turadi.
     */
    private fun tozaFonmi(oq: Maska, q: Bolak, chet: Double = 0.35): Double {
        val dx = (q.w * chet).toInt() + 3
        val dy = (q.h * chet).toInt() + 3
        val x0 = maxOf(0, q.x - dx); val y0 = maxOf(0, q.y - dy)
        val x1 = minOf(oq.width, q.right + dx); val y1 = minOf(oq.height, q.bottom + dy)
        if (x1 <= x0 || y1 <= y0) return 0.0
        var n = 0; var bor = 0
        for (y in y0 until y1) for (x in x0 until x1) { n++; if (oq.bits[y * oq.width + x]) bor++ }
        return if (n == 0) 0.0 else bor.toDouble() / n
    }

    fun burchaklar(f: Frame, minRankH: Int = 40, minOqlik: Double = 0.48): List<Burchak> {
        val oqM = oq(f)
        val oqKeng = oqM.kengaytir(8)
        val topildi = ArrayList<Burchak>()

        for ((rang, m) in listOf("qora" to qora(f), "qizil" to qizil(f))) {
            val ink = m va oqKeng
            val parts = oninchiniBirlashtir(bolaklar(ink, 100, 12000))
            val ranks = parts.filter { it.h >= minRankH && 0.9 * it.h >= it.w }
            for (rk in ranks) {
                val cx = rk.cx
                var nomzod: Bolak? = null
                for (s in parts) {
                    if (s === rk) continue
                    val gap = s.y - rk.bottom
                    if (gap.toDouble() in (-0.15 * rk.h)..(0.70 * rk.h)
                        && Math.abs(s.cx - cx) <= 0.70 * rk.w
                        && s.h >= 0.30 * rk.h && s.h <= 0.90 * rk.h
                        && s.w <= 0.95 * rk.h
                    ) {
                        if (nomzod == null || s.y < nomzod.y) nomzod = s
                    }
                }
                // Kesish XOM rang maskasi bo'yicha: oq bilan kesishtirilgani
                // belgining chekkasini yo'qotadi va botiq boshqa joyda chiqadi.
                val mast = (nomzod ?: continue).let { mastKes(it, rk, m) }
                val x0 = minOf(rk.x, mast.x)
                val quti = Bolak(x0, rk.y, maxOf(rk.right, mast.right) - x0, mast.bottom - rk.y, 0)
                val oqlik = tozaFonmi(oqM, quti)
                if (oqlik < minOqlik) continue
                topildi.add(Burchak(rang, rk, mast, quti, oqlik))
            }
        }

        // Bir xil joydagi takrorlar
        val natija = ArrayList<Burchak>()
        for (t in topildi.sortedByDescending { it.quti.h }) {
            val b = t.quti
            if (natija.any { Math.abs(b.x - it.quti.x) < 0.6 * b.w && Math.abs(b.y - it.quti.y) < 0.6 * b.h }) continue
            natija.add(t)
        }
        return olchamFiltri(natija, f.height).sortedWith(compareBy({ it.quti.y }, { it.quti.x }))
    }

    /** Bitta zonadagi kartalar bir xil o'lchamda — o'rtachadan keskin farq qilgani soxta. */
    private fun olchamFiltri(topildi: List<Burchak>, kadrBalandligi: Int, chidam: Double = 0.18): List<Burchak> {
        val zonalar = topildi.groupBy {
            val yc = it.quti.cy / kadrBalandligi
            if (yc > 0.66) "qol" else if (yc > 0.25) "stol" else "yuqori"
        }
        val out = ArrayList<Burchak>()
        for ((_, ts) in zonalar) {
            if (ts.size < 3) { out.addAll(ts); continue }
            val hs = ts.map { it.quti.h }.sorted()
            val orta = hs[hs.size / 2]
            out.addAll(ts.filter { Math.abs(it.quti.h - orta) <= chidam * orta })
        }
        return out
    }

    /** Kozir kartasi yonboshlab yotadi — hududni burib, o'sha qidiruv ishlatiladi. */
    fun kozirBurchagi(f: Frame): Pair<Burchak, Frame>? {
        val burilgan = f.crop(KOZIR_ROI.toPixels(f.width, f.height)).rotate90()
        val bs = burchaklar(burilgan, minRankH = 25, minOqlik = 0.30)
        val eng = bs.maxByOrNull { it.quti.h } ?: return null
        return eng to burilgan
    }

    // --- zaxira soni ---

    fun zaxiraBolaklari(f: Frame): List<Bolak> {
        val p = ZAXIRA_ROI.toPixels(f.width, f.height)
        val sub = f.crop(p)
        val m = oqMatn(sub)
        return bolaklar(m, 80).filter { it.h >= 0.5 * p.h && it.w <= 1.2 * it.h }
            .map { Bolak(it.x + p.x, it.y + p.y, it.w, it.h, it.maydon) }
            .sortedBy { it.x }
    }

    // --- hodisa pufakchalari ---

    data class PufakNomzodi(val kim: String, val rang: String, val matn: Bolak)

    fun pufakNomzodlari(f: Frame): List<PufakNomzodi> {
        val oqP = oqPufak(f)
        val sariqM = sariq(f)
        val qoraM = qora(f)
        val out = ArrayList<PufakNomzodi>()
        for ((kim, cx, cy) in PUFAK_JOYLARI) {
            val x0 = ((cx - PUFAK_ENI / 2) * f.width).toInt().coerceAtLeast(0)
            val x1 = ((cx + PUFAK_ENI / 2) * f.width).toInt().coerceAtMost(f.width)
            val y0 = ((cy - PUFAK_BOYI / 2) * f.height).toInt().coerceAtLeast(0)
            val y1 = ((cy + PUFAK_BOYI / 2) * f.height).toInt().coerceAtMost(f.height)
            val eniR = x1 - x0; val boyiR = y1 - y0
            for ((rang, m) in listOf("sariq" to sariqM, "oq" to oqP)) {
                val kesim = Maska(eniR, boyiR, BooleanArray(eniR * boyiR) { i ->
                    m.bits[(y0 + i / eniR) * f.width + x0 + i % eniR]
                })
                val nomzod = bolaklar(kesim, 2000).firstOrNull {
                    it.w > 0.25 * eniR && it.w < 0.85 * eniR && it.h > 0.30 * boyiR && it.h < 0.80 * boyiR
                } ?: continue
                val bx = x0 + nomzod.x; val by = y0 + nomzod.y
                // Chet qoldiriladi: pufakcha ostidagi kartalar va dumi matnga qo'shilmasin.
                val ix = (0.10 * nomzod.w).toInt(); val iy = (0.12 * nomzod.h).toInt()
                var mnX = Int.MAX_VALUE; var mnY = Int.MAX_VALUE
                var mxX = -1; var mxY = -1; var soni = 0
                for (y in by + iy until by + nomzod.h - iy) {
                    for (x in bx + ix until bx + nomzod.w - ix) {
                        if (!qoraM.bits[y * f.width + x]) continue
                        soni++
                        if (x < mnX) mnX = x; if (x > mxX) mxX = x
                        if (y < mnY) mnY = y; if (y > mxY) mxY = y
                    }
                }
                if (soni < 150 || mxX < 0) continue
                out.add(PufakNomzodi(kim, rang, Bolak(mnX, mnY, mxX - mnX + 1, mxY - mnY + 1, soni)))
            }
        }
        return out
    }

    // --- himoyachi (yashil halqa) ---

    /**
     * Har o'yinchi avatarini rangli halqa o'rab turadi. O'lchov shuni ko'rsatdi:
     * har payt faqat bitta o'yinchi yashil va u tur davomida o'zgarmaydi —
     * aynan o'sha kartani oladi yoki qoplaydi. Ya'ni yashil halqa = himoyachi.
     */
    fun himoyachi(f: Frame, chegara: Double = 0.12): String? {
        var eng: String? = null
        var engBall = chegara
        for ((kim, roi) in AVATARLAR) {
            val p = roi.toPixels(f.width, f.height)
            val q = maxOf(3, (0.09 * maxOf(p.w, p.h)).toInt())
            var yashil = 0; var qizilS = 0; var n = 0
            for (y in 0 until p.h) {
                for (x in 0 until p.w) {
                    val chetda = y < q || y >= p.h - q || x < q || x >= p.w - q
                    if (!chetda) continue
                    n++
                    val i = (p.y + y) * f.width + p.x + x
                    val r = f.r(i); val g = f.g(i); val b = f.b(i)
                    if (g > 140 && g - r > 40 && g - b > 60) yashil++
                    if (r > 170 && r - g > 60 && r - b > 40) qizilS++
                }
            }
            if (n == 0) continue
            val y = yashil.toDouble() / n
            if (y > engBall && y > qizilS.toDouble() / n) { eng = kim; engBall = y }
        }
        return eng
    }
}
