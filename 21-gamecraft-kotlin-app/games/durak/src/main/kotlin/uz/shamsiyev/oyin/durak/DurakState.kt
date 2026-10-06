package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*
import kotlin.random.Random

/** Qoida sozlamalari. Hozir: podkidnoy, o'tkazish yo'q. */
data class DurakRules(
    val playerCount: Int = 3,
    val handSize: Int = 6,
    /** Bir turda stolga tushadigan maksimal hujum kartasi. */
    val maxAttacks: Int = 6,
    /** Himoyachi olganidan keyin ham qo'shib tashlash mumkinmi. */
    val throwInAfterTake: Boolean = true,
) {
    init {
        require(playerCount in 2..6) { "o'yinchi soni 2..6 bo'lishi kerak" }
    }
}

enum class Phase {
    /** Kimdir hujum qiladi yoki pas aytadi. */
    ATTACK,
    /** Himoyachi qoplaydi yoki oladi. */
    DEFEND,
    /** Himoyachi olgan — qolganlar yana qo'shib tashlashi mumkin. */
    THROW_IN,
    /** O'yin tugadi. */
    OVER,
}

const val NO_CARD = -1

/**
 * To'liq ma'lumotli holat: hamma qo'l ko'rinadi.
 * Bu simulyatsiya uchun. Haqiqiy o'yinda raqib qo'li noma'lum —
 * u yerda [DurakView] ishlatiladi va undan shu holatning taxminlari yasaladi.
 */
class DurakState(
    val rules: DurakRules,
    val trumpSuit: Int,
    val deck: IntArray,
    var deckPos: Int,
    val hands: LongArray,
    var discard: CardSet,
    val attacks: IntArray,
    val defends: IntArray,
    var tableCount: Int,
    var attacker: Int,
    var defender: Int,
    var toMove: Int,
    var phase: Phase,
    val passed: BooleanArray,
    val out: BooleanArray,
    var boutLimit: Int,
    var durak: Int,
) {
    val codec: CardCodec get() = DECK36

    /** Zaxirada qolgan karta soni (ochiq yotgan kozir kartasi ham shunga kiradi). */
    val deckLeft: Int get() = deck.size - deckPos

    /** Pastda ochiq yotgan kozir kartasi — hamma ko'radi. */
    val trumpCard: Int get() = deck.last()

    fun handOf(player: Int): CardSet = hands[player]

    fun copy() = DurakState(
        rules, trumpSuit, deck, deckPos, hands.copyOf(), discard,
        attacks.copyOf(), defends.copyOf(), tableCount,
        attacker, defender, toMove, phase, passed.copyOf(), out.copyOf(), boutLimit, durak,
    )

    /** [defence] kartasi [attack] kartasini qoplay oladimi. */
    fun beats(defence: Int, attack: Int): Boolean {
        val ds = DECK36.suit(defence)
        val `as` = DECK36.suit(attack)
        return if (ds == `as`) DECK36.rank(defence) > DECK36.rank(attack)
        else ds == trumpSuit
    }

    /** Stolda turgan barcha darajalar — qo'shib tashlash shu darajalar bilan cheklangan. */
    fun ranksOnTable(): Int {
        var mask = 0
        for (i in 0 until tableCount) {
            mask = mask or (1 shl DECK36.rank(attacks[i]))
            if (defends[i] != NO_CARD) mask = mask or (1 shl DECK36.rank(defends[i]))
        }
        return mask
    }

    /** Qoplanmagan hujum kartasining o'rni, yo'q bo'lsa -1. */
    fun undefendedIndex(): Int {
        for (i in 0 until tableCount) if (defends[i] == NO_CARD) return i
        return -1
    }

    fun activePlayers(): Int = out.count { !it }

    override fun toString(): String = buildString {
        append("kozir=${DECK36.suitNames[trumpSuit]} zaxira=$deckLeft ")
        append("navbat=$toMove ($phase) hujum=$attacker himoya=$defender\n")
        append("stol: ")
        for (i in 0 until tableCount) {
            append(DECK36.name(attacks[i]))
            if (defends[i] != NO_CARD) append("/${DECK36.name(defends[i])}")
            append("  ")
        }
        append("\n")
        for (p in hands.indices) {
            append("  o'yinchi $p${if (out[p]) " (chiqdi)" else ""}: ${hands[p].render(DECK36)}\n")
        }
    }

    companion object {
        /** Yangi o'yin: taxlam aralashtiriladi, har kimga 6 tadan, pastdagi karta kozir. */
        fun newGame(rules: DurakRules = DurakRules(), rng: Random = Random.Default): DurakState {
            val deck = DECK36.allCards().also { it.shuffle(rng) }
            val trumpSuit = DECK36.suit(deck.last())

            val hands = LongArray(rules.playerCount)
            var pos = 0
            repeat(rules.handSize) {
                for (p in 0 until rules.playerCount) {
                    hands[p] = hands[p].with(deck[pos++])
                }
            }

            // Birinchi hujumchi — eng past kozir kimda bo'lsa, o'sha. Topilmasa 0-o'yinchi.
            var attacker = 0
            var bestRank = Int.MAX_VALUE
            for (p in 0 until rules.playerCount) {
                hands[p].forEachCard { c ->
                    if (DECK36.suit(c) == trumpSuit && DECK36.rank(c) < bestRank) {
                        bestRank = DECK36.rank(c); attacker = p
                    }
                }
            }
            val defender = (attacker + 1) % rules.playerCount

            return DurakState(
                rules = rules,
                trumpSuit = trumpSuit,
                deck = deck,
                deckPos = pos,
                hands = hands,
                discard = EMPTY_CARDS,
                attacks = IntArray(rules.maxAttacks) { NO_CARD },
                defends = IntArray(rules.maxAttacks) { NO_CARD },
                tableCount = 0,
                attacker = attacker,
                defender = defender,
                toMove = attacker,
                phase = Phase.ATTACK,
                passed = BooleanArray(rules.playerCount),
                out = BooleanArray(rules.playerCount),
                boutLimit = minOf(rules.maxAttacks, hands[defender].count()),
                durak = NO_CARD,
            )
        }
    }
}
