package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*

/**
 * Kadrlar ketma-ketligidan o'yin oqimini tiklaydi.
 *
 * Bitta kadr faqat "hozir nima ko'rinyapti" ni aytadi. O'yin uchun esa tarix
 * kerak: bitoga ketgan kartalar ekranda umuman ko'rinmaydi, lekin ularsiz
 * maslahat zaif. Shuning uchun ilova o'yinni BOSHIDAN kuzatishi kerak;
 * o'rtadan ulansa, bitoga ketganlar noma'lum qoladi.
 *
 * Uch narsa o'zini o'zi tekshiradi:
 *  - bitoga ketgan karta qaytib kelmaydi;
 *  - 36 ta karta yo'qolmaydi (qolgani raqiblarda);
 *  - zaxira soni faqat kamayadi, ko'tarilsa - yangi o'yin.
 */
class Kuzatuv(private val raqiblarSoni: Int = 2, private val tinchlik: Int = 2) {

    data class Juft(val hujum: String, val qoplagan: String?)

    data class Yozuv(val vaqt: Double, val matn: String)

    private val tarix = ArrayDeque<EkranHolati>()
    val jurnal = ArrayList<Yozuv>()
    var ziddiyat = 0
        private set

    var kozir: String? = null; private set
    var bitoga = LinkedHashSet<String>(); private set
    var qol = emptySet<String>(); private set
    var stol = emptySet<String>(); private set
    var juftlar = emptyList<Juft>(); private set
    var zaxira: Int? = null; private set
    var himoyachi: String? = null; private set
    var beruBormi = false; private set
    var faolOyinchi: String? = null; private set
    private var raqib = IntArray(raqiblarSoni) { 6 }
    private var turHodisalari = ArrayList<Pair<String, String>>()
    private var ekrandagi = emptySet<Pair<String, String>>()

    fun yangiOyin() {
        kozir = null
        bitoga = LinkedHashSet()
        qol = emptySet()
        stol = emptySet()
        juftlar = emptyList()
        zaxira = null
        himoyachi = null
        beruBormi = false
        faolOyinchi = null
        raqib = IntArray(raqiblarSoni) { 6 }
        turHodisalari = ArrayList()
        ekrandagi = emptySet()
    }

    /** Oxirgi kadrlarda kamida `tinchlik` marta ko'ringan kartalar. */
    private fun barqaror(tanla: (EkranHolati) -> Collection<String>): Set<String> {
        if (tarix.size < tinchlik) return tarix.lastOrNull()?.let { tanla(it).toSet() } ?: emptySet()
        val son = HashMap<String, Int>()
        for (h in tarix) for (k in tanla(h).toSet()) son[k] = (son[k] ?: 0) + 1
        return son.filterValues { it >= tinchlik }.keys
    }

    fun qadam(h: EkranHolati, vaqt: Double = 0.0) {
        val oldingiStol = stol
        tarix.addLast(h)
        while (tarix.size > 3) tarix.removeFirst()

        // Kozir o'yin davomida o'zgarmaydi - bir marta o'qilsa yetadi.
        if (h.kozir != null && kozir == null) {
            kozir = h.kozir
            jurnal.add(Yozuv(vaqt, "kozir ${h.kozir}"))
        }

        // Zaxira soni faqat kamayadi; ko'tarilsa - yangi o'yin boshlangan.
        if (h.zaxira != null) {
            val oldingi = zaxira
            if (oldingi != null && h.zaxira > oldingi + 1) {
                jurnal.add(Yozuv(vaqt, "YANGI O'YIN (zaxira $oldingi -> ${h.zaxira})"))
                yangiOyin()
            }
            zaxira = h.zaxira
        }

        beruBormi = h.beruBormi
        faolOyinchi = h.faolOyinchi

        val yangiStol = barqaror { o -> o.stol.mapNotNull { it.karta } }
        qol = barqaror { it.qol } - yangiStol - bitoga

        // Stol bo'shadi - tur tugadi. Kartalar qayerga ketdi?
        if (oldingiStol.isNotEmpty() && yangiStol.isEmpty()) {
            val olgan = turHodisalari.firstOrNull { it.second == "oldim" }
            if (olgan != null) {
                val egasi = olgan.first
                if (egasi == "men") {
                    jurnal.add(Yozuv(vaqt, "men oldim: ${oldingiStol.size} karta"))
                } else {
                    val i = if (egasi == "chap") 0 else 1
                    if (i < raqib.size) raqib[i] += oldingiStol.size
                    jurnal.add(Yozuv(vaqt, "$egasi oldi: ${oldingiStol.size} karta"))
                }
            } else {
                bitoga.addAll(oldingiStol)
                jurnal.add(Yozuv(vaqt, "bito: ${oldingiStol.sorted().joinToString(" ")} (jami ${bitoga.size})"))
            }
            turHodisalari = ArrayList()
        }

        if (h.beruBormi) {
            himoyachi = "men"
        } else if (h.himoyachi != null) {
            himoyachi = h.himoyachi
        } else if (himoyachi == "men" && yangiStol.isEmpty()) {
            himoyachi = null
        }
        stol = yangiStol
        juftlar = juftlarniTop(h.stol.filter { it.karta in yangiStol }, yangiStol)

        // Pufakcha ekranda bir necha soniya turadi. Shuning uchun hodisa faqat
        // PAYDO BO'LGAN payti qayd qilinadi - aks holda keyingi turga ham o'tib ketadi.
        val hozir = h.hodisalar.map { it.kim to it.hodisa }.toSet()
        for (juft in hozir - ekrandagi) turHodisalari.add(juft)
        ekrandagi = hozir

        // Bitoga ketgan karta qaytib kelmaydi. Kelsa - biror joyda xato o'qilgan.
        // Bunda ko'z bilan ko'rinayotganiga ishonamiz: u to'g'ridan-to'g'ri kuzatuv,
        // bitoga ketganlar esa xulosa.
        val qaytganlar = stol intersect bitoga
        if (qaytganlar.isNotEmpty()) {
            ziddiyat += qaytganlar.size
            bitoga.removeAll(qaytganlar)
            jurnal.add(Yozuv(vaqt, "ZIDDIYAT: ${qaytganlar.sorted().joinToString(" ")} bitodan qaytdi " +
                    "- xato o'qilgan, bitodan chiqarildi"))
        }
    }

    /**
     * Stoldagi kartalarni (hujum, qoplagan) juftlariga ajratadi.
     * Qoplagan karta hujum kartasining ustiga o'ngga-pastga siljib tushadi -
     * bu siljish barqaror, shuning uchun juftlikni joylashuvdan aniqlash mumkin.
     */
    private fun juftlarniTop(korinayotgan: List<OqilganKarta>, barqarorStol: Set<String>): List<Juft> {
        val ks = korinayotgan.sortedBy { it.quti.x }
        val band = HashSet<Int>()
        val out = ArrayList<Juft>()
        for (i in ks.indices) {
            if (i in band) continue
            var qoplagan: String? = null
            for (j in i + 1 until ks.size) {
                if (j in band) continue
                val h = (ks[i].quti.h + ks[j].quti.h) / 2.0
                val dx = (ks[j].quti.x - ks[i].quti.x) / h
                val dy = (ks[j].quti.y - ks[i].quti.y) / h
                if (dx in 0.25..0.75 && dy in 0.02..0.45) {
                    qoplagan = ks[j].karta
                    band.add(j)
                    break
                }
            }
            band.add(i)
            out.add(Juft(ks[i].karta!!, qoplagan))
        }
        // Silliqlangan to'plamda bor-u, shu kadrda ko'rinmagan karta "qoplanmagan" bo'ladi.
        val topilgan = out.flatMap { listOfNotNull(it.hujum, it.qoplagan) }.toSet()
        for (yoq in (barqarorStol - topilgan).sorted()) out.add(Juft(yoq, null))
        return out
    }

    /** Saqlanish qonuni: 36 tadan ko'ringanini ayirsak, qolgani raqiblarda. */
    fun raqiblardagiJami(): Int =
        maxOf(0, DECK36.size - qol.size - stol.size - bitoga.size - (zaxira ?: 0))

    /** Dvigatel tushunadigan ko'rinish. */
    fun dvigatelUchun(): DurakView? {
        val kozirNomi = kozir ?: return null
        val kozirKarta = kartaOqi(kozirNomi)
        val rules = DurakRules(playerCount = 1 + raqiblarSoni)

        var qolSet = EMPTY_CARDS
        for (k in qol) qolSet = qolSet.with(kartaOqi(k))
        var bitoSet = EMPTY_CARDS
        for (k in bitoga) bitoSet = bitoSet.with(kartaOqi(k))

        val attacks = IntArray(rules.maxAttacks) { NO_CARD }
        val defends = IntArray(rules.maxAttacks) { NO_CARD }
        juftlar.take(rules.maxAttacks).forEachIndexed { i, j ->
            attacks[i] = kartaOqi(j.hujum)
            j.qoplagan?.let { defends[i] = kartaOqi(it) }
        }

        // Alohida sonlar aniq emas - saqlanish qonuni bilan moslanadi.
        val jami = raqiblardagiJami()
        val taqsim = raqib.copyOf()
        val yigindi = taqsim.sum()
        if (yigindi > 0) {
            val k = jami.toDouble() / yigindi
            for (i in taqsim.indices) taqsim[i] = maxOf(0, Math.round(taqsim[i] * k).toInt())
        }
        if (taqsim.isNotEmpty()) taqsim[0] += jami - taqsim.sum()

        val defIdx = when {
            beruBormi || himoyachi == "men" -> 0
            himoyachi == "chap" -> 1
            himoyachi == "ong" -> 2
            else -> 1
        }

        val atkIdx = when (defIdx) {
            0 -> if (faolOyinchi == "chap") 1 else 2
            1 -> 0
            2 -> if (faolOyinchi == "men") 0 else 1
            else -> 0
        }

        val ochiqHujum = juftlar.any { it.qoplagan == null }
        val phase = if (ochiqHujum) Phase.DEFEND else Phase.ATTACK

        val toMove = when {
            beruBormi -> 0
            ochiqHujum -> defIdx
            faolOyinchi == "chap" -> 1
            faolOyinchi == "ong" -> 2
            faolOyinchi == "men" -> 0
            else -> atkIdx
        }

        return DurakView(
            rules = rules,
            me = 0,
            trumpSuit = DECK36.suit(kozirKarta),
            trumpCard = if ((zaxira ?: 0) > 0) kozirKarta else NO_CARD,
            deckLeft = zaxira ?: 0,
            myHand = qolSet,
            discard = bitoSet,
            handCounts = IntArray(rules.playerCount) { if (it == 0) qol.size else taqsim.getOrElse(it - 1) { 6 } },
            attacks = attacks,
            defends = defends,
            tableCount = minOf(juftlar.size, rules.maxAttacks),
            attacker = atkIdx,
            defender = defIdx,
            toMove = toMove,
            phase = phase,
            passed = BooleanArray(rules.playerCount),
            out = BooleanArray(rules.playerCount),
            boutLimit = minOf(rules.maxAttacks, taqsim.getOrElse(0) { 6 }.coerceAtLeast(1)),
        )
    }
}
