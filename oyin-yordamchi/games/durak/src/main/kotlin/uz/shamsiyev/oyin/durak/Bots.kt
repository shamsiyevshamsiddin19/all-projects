package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*
import kotlin.random.Random

interface DurakBot {
    val name: String
    fun chooseMove(state: DurakState, moves: IntArray, me: Int): Int
}

/** Tasodifiy o'ynaydi — faqat qoidalarni sinash va o'lchov uchun asos. */
class RandomBot(private val rng: Random = Random.Default) : DurakBot {
    override val name = "tasodifiy"
    override fun chooseMove(state: DurakState, moves: IntArray, me: Int) = moves[rng.nextInt(moves.size)]
}

/**
 * Oddiy qoidali bot. Faqat ko'rinadigan ma'lumotdan foydalanadi
 * (o'z qo'li, stol, kozir, zaxira soni) — shuning uchun maslahatchi sifatida ham ishlatsa bo'ladi.
 *
 * Monte-Carlo versiyasi aynan shuni yengishi kerak — o'lchov shu.
 */
class HeuristicBot : DurakBot {
    override val name = "qoidali"

    /** Karta qiymati: kozir ancha qimmat. */
    private fun value(state: DurakState, card: Int): Int {
        val r = DECK36.rank(card)
        return if (DECK36.suit(card) == state.trumpSuit) r + 20 else r
    }

    override fun chooseMove(state: DurakState, moves: IntArray, me: Int): Int {
        return when (state.phase) {
            Phase.DEFEND -> chooseDefence(state, moves)
            else -> chooseAttack(state, moves)
        }
    }

    private fun chooseDefence(state: DurakState, moves: IntArray): Int {
        val idx = state.undefendedIndex()
        val attack = state.attacks[idx]
        var best = NO_CARD
        var bestValue = Int.MAX_VALUE
        for (m in moves) {
            if (!Move.isDefend(m)) continue
            val v = value(state, Move.card(m))
            if (v < bestValue) { bestValue = v; best = m }
        }
        if (best == NO_CARD) return Move.TAKE

        // Past kartani qoplash uchun kozir sarflash — zaxira ko'p bo'lsa ziyon.
        val card = Move.card(best)
        val spendingTrump = DECK36.suit(card) == state.trumpSuit && DECK36.suit(attack) != state.trumpSuit
        if (spendingTrump && state.deckLeft > 6 && DECK36.rank(attack) <= 1 && state.tableCount == 1) {
            return Move.TAKE
        }
        return best
    }

    private fun chooseAttack(state: DurakState, moves: IntArray): Int {
        var best = NO_CARD
        var bestValue = Int.MAX_VALUE
        for (m in moves) {
            if (!Move.isAttack(m)) continue
            val v = value(state, Move.card(m))
            if (v < bestValue) { bestValue = v; best = m }
        }
        if (best == NO_CARD) return Move.PASS

        val card = Move.card(best)
        val isTrump = DECK36.suit(card) == state.trumpSuit
        val defenderCards = state.hands[state.defender].count()

        // Zaxira to'la paytda kozir bilan hujum qilish isrof — pas aytamiz.
        if (isTrump && state.deckLeft > 4 && state.tableCount > 0) return Move.PASS

        // Himoyachining kartasi tugayotgan bo'lsa — bosim, qo'lni bo'shatamiz.
        if (defenderCards <= 1 && Move.PASS in moves && state.tableCount > 0 && isTrump) return best

        return best
    }
}

private operator fun IntArray.contains(value: Int): Boolean {
    for (v in this) if (v == value) return true
    return false
}
