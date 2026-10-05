package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*

/**
 * Ekrandan o'qilgan holatni qabul qilib, maslahat beradi.
 *
 * Ko'z qismi (hozircha Python) shu ko'rinishda holat uzatadi:
 *   --kozir 8C --qol 10C,JC,JD,KC,QH --hujum 6S --qopla KS
 *   --zaxira 2 --bito 6D,7H --raqiblar 5,6 --rol himoya
 */
private val MAST = mapOf('S' to 0, 'C' to 1, 'D' to 2, 'H' to 3)

fun kartaOqi(matn: String): Int {
    val t = matn.trim().uppercase()
    val suit = MAST[t.last()] ?: error("mast tanilmadi: $matn")
    val rank = DECK36.rankNames.indexOf(t.dropLast(1))
    require(rank >= 0) { "daraja tanilmadi: $matn" }
    return DECK36.card(rank, suit)
}

private fun ro(a: Array<String>, kalit: String): String? {
    val i = a.indexOf("--$kalit")
    return if (i >= 0 && i + 1 < a.size) a[i + 1] else null
}

private fun kartalar(s: String?): List<Int> =
    s?.split(",")?.map { it.trim() }?.filter { it.isNotEmpty() && it != "-" }?.map { kartaOqi(it) } ?: emptyList()

fun main(args: Array<String>) {
    val kozir = kartaOqi(ro(args, "kozir") ?: error("--kozir kerak"))
    val qol = kartalar(ro(args, "qol"))
    val hujumlar = kartalar(ro(args, "hujum"))
    val qoplaganlar = (ro(args, "qopla") ?: "").split(",").map { it.trim() }
    val zaxira = ro(args, "zaxira")?.toIntOrNull() ?: 0
    val bitoga = kartalar(ro(args, "bito"))
    val raqiblar = (ro(args, "raqiblar") ?: "6,6").split(",").map { it.trim().toInt() }
    val rol = ro(args, "rol") ?: "hujum"

    val rules = DurakRules(playerCount = 1 + raqiblar.size)
    val attacks = IntArray(rules.maxAttacks) { NO_CARD }
    val defends = IntArray(rules.maxAttacks) { NO_CARD }
    hujumlar.forEachIndexed { i, c -> if (i < rules.maxAttacks) attacks[i] = c }
    qoplaganlar.forEachIndexed { i, s ->
        if (i < rules.maxAttacks && s.isNotEmpty() && s != "-" && s.lowercase() != "none") {
            defends[i] = kartaOqi(s)
        }
    }

    var qolSet = EMPTY_CARDS
    qol.forEach { qolSet = qolSet.with(it) }
    var bitoSet = EMPTY_CARDS
    bitoga.forEach { bitoSet = bitoSet.with(it) }

    // 0 - men. Himoyachi bo'lsam hujumchi boshqa o'yinchi, aks holda men hujum qilaman.
    val menHimoya = rol.startsWith("him")
    val hujumchi = if (menHimoya) rules.playerCount - 1 else 0
    val himoyachi = if (menHimoya) 0 else 1

    val view = DurakView(
        rules = rules,
        me = 0,
        trumpSuit = DECK36.suit(kozir),
        trumpCard = if (zaxira > 0) kozir else NO_CARD,
        deckLeft = zaxira,
        myHand = qolSet,
        discard = bitoSet,
        handCounts = IntArray(rules.playerCount) { if (it == 0) qol.size else raqiblar[it - 1] },
        attacks = attacks,
        defends = defends,
        tableCount = hujumlar.size,
        attacker = hujumchi,
        defender = himoyachi,
        toMove = 0,
        phase = if (menHimoya) Phase.DEFEND else Phase.ATTACK,
        passed = BooleanArray(rules.playerCount),
        out = BooleanArray(rules.playerCount),
        boutLimit = minOf(rules.maxAttacks, raqiblar.getOrElse(0) { 6 }),
    )

    println("kozir ${DECK36.suitNames[view.trumpSuit]} · zaxira $zaxira · bitoda ${bitoga.size} · " +
            if (menHimoya) "himoya" else "hujum")
    println("qo'lim: ${qolSet.render(DECK36)}")
    print("stol: ")
    for (i in hujumlar.indices) {
        print(DECK36.name(attacks[i]))
        if (defends[i] != NO_CARD) print("/${DECK36.name(defends[i])}")
        print("  ")
    }
    println("\n")

    val advice = DurakAdvisor().advise(view)
    println("  >>> ${advice.headline.uppercase()}")
    println("      ${advice.reason}")
    advice.caveat?.let { println("      (!) $it") }
}
