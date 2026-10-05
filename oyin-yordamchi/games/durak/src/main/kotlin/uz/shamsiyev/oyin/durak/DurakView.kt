package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*
import kotlin.random.Random

/**
 * Haqiqiy o'yinda ko'rinadigan narsa: o'z qo'lim, stol, kozir, zaxira soni,
 * raqiblarda nechta karta borligi va bitoga ketgan kartalar.
 * Raqibning qo'lida AYNAN nima borligi noma'lum.
 */
class DurakView(
    val rules: DurakRules,
    val me: Int,
    val trumpSuit: Int,
    val trumpCard: Int,
    val deckLeft: Int,
    val myHand: CardSet,
    val discard: CardSet,
    val handCounts: IntArray,
    val attacks: IntArray,
    val defends: IntArray,
    val tableCount: Int,
    val attacker: Int,
    val defender: Int,
    val toMove: Int,
    val phase: Phase,
    val passed: BooleanArray,
    val out: BooleanArray,
    val boutLimit: Int,
) {
    /** Hali qayerdaligi noma'lum kartalar: raqiblar qo'lida yoki zaxirada. */
    fun unseen(): CardSet {
        var seen = myHand or discard
        for (i in 0 until tableCount) {
            seen = seen.with(attacks[i])
            if (defends[i] != NO_CARD) seen = seen.with(defends[i])
        }
        if (deckLeft > 0 && trumpCard != NO_CARD) seen = seen.with(trumpCard)
        var all = EMPTY_CARDS
        for (c in 0 until DECK36.size) all = all.with(c)
        return all and seen.inv()
    }

    /**
     * Noma'lum kartalarni tasodifiy tarqatib, to'liq holat yasaydi.
     * Monte-Carlo shu taxminlarni yuzlab marta yasab o'ynab ko'radi.
     */
    fun sample(rng: Random): DurakState {
        val pool = unseen().toList().toIntArray()
        pool.shuffle(rng)

        val hands = LongArray(rules.playerCount)
        hands[me] = myHand
        var pos = 0
        for (p in 0 until rules.playerCount) {
            if (p == me) continue
            repeat(handCounts[p]) { hands[p] = hands[p].with(pool[pos++]) }
        }

        // Qolgani zaxira; ochiq kozir kartasi eng pastda turadi.
        val rest = pool.copyOfRange(pos, pool.size)
        val deck = if (deckLeft > 0 && trumpCard != NO_CARD) rest + trumpCard else rest

        return DurakState(
            rules = rules,
            trumpSuit = trumpSuit,
            deck = deck,
            deckPos = 0,
            hands = hands,
            discard = discard,
            attacks = attacks.copyOf(),
            defends = defends.copyOf(),
            tableCount = tableCount,
            attacker = attacker,
            defender = defender,
            toMove = toMove,
            phase = phase,
            passed = passed.copyOf(),
            out = out.copyOf(),
            boutLimit = boutLimit,
            durak = NO_CARD,
        )
    }
}

/** To'liq holatdan [me] ko'rayotgan manzarani ajratib oladi (qolgan qo'llar yashiriladi). */
fun DurakState.toView(me: Int) = DurakView(
    rules = rules,
    me = me,
    trumpSuit = trumpSuit,
    trumpCard = if (deckLeft > 0) trumpCard else NO_CARD,
    deckLeft = deckLeft,
    myHand = hands[me],
    discard = discard,
    handCounts = IntArray(rules.playerCount) { hands[it].count() },
    attacks = attacks.copyOf(),
    defends = defends.copyOf(),
    tableCount = tableCount,
    attacker = attacker,
    defender = defender,
    toMove = toMove,
    phase = phase,
    passed = passed.copyOf(),
    out = out.copyOf(),
    boutLimit = boutLimit,
)

/** Stolda nechta karta qoplanmagan. */
fun DurakView.undefendedCount(): Int {
    var n = 0
    for (i in 0 until tableCount) if (defends[i] == NO_CARD) n++
    return n
}
