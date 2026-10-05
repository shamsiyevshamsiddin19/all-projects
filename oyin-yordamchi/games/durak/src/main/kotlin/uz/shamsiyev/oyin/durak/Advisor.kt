package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*
import uz.shamsiyev.oyin.core.Advice
import kotlin.random.Random

/**
 * Hisobni odam tushunadigan maslahatga aylantiradi.
 * Overlay oynasi faqat shu natijani ko'rsatadi.
 */
class DurakAdvisor(
    private val bot: PimcBot = PimcBot(samples = 80, budgetMillis = 350, rng = Random.Default),
) {
    fun advise(view: DurakView): Advice {
        val state = view.sample(Random.Default)
        val moves = state.legalMoves()
        if (moves.isEmpty()) return Advice("navbat sizda emas", confidence = 1.0)
        if (moves.size == 1) {
            return Advice(headline(moves[0], view), reason = "boshqa variant yo'q", confidence = 1.0)
        }

        val ranked = bot.rank(view, moves)
        val (bestMove, bestScore) = ranked[0]
        val secondScore = ranked.getOrNull(1)?.second ?: 0.0
        val gap = bestScore - secondScore

        return Advice(
            headline = headline(bestMove, view),
            reason = reason(bestMove, view, bestScore),
            // Farq katta bo'lsa — aniq yurish; kichik bo'lsa — variantlar deyarli teng.
            confidence = (0.5 + gap * 2.0).coerceIn(0.0, 1.0),
            caveat = if (gap < 0.03) "variantlar deyarli teng" else null,
        )
    }

    private fun headline(move: Int, view: DurakView): String = when {
        move == Move.PASS ->
            if (view.phase == Phase.THROW_IN) "qo'shma"
            else if (view.undefendedCount() == 0) "bito bos"
            else "qo'shma"
        move == Move.TAKE -> "ol"
        Move.isAttack(move) -> "${DECK36.name(Move.card(move))} bilan yur"
        else -> "${DECK36.name(Move.card(move))} bilan qopla"
    }

    private fun reason(move: Int, view: DurakView, score: Double): String {
        val chance = "%.0f".format(score * 100) + "% omon"
        if (move == Move.TAKE) return "qoplash juda qimmat - olgan foydali | $chance"
        if (move == Move.PASS) return "qo'shimcha karta berish ziyon | $chance"

        val card = Move.card(move)
        val isTrump = DECK36.suit(card) == view.trumpSuit
        val trumpsLeft = view.myHand.toList().count { DECK36.suit(it) == view.trumpSuit }

        // Sabab haqiqiy tanlovdan chiqarilади: qo'lda bundan arzonrog'i bormi?
        val cheaper = view.myHand.toList().count { value(view, it) < value(view, card) }

        val core = when {
            Move.isAttack(move) && isTrump && view.deckLeft == 0 -> "zaxira tugadi, kozir bilan bosiladi"
            Move.isAttack(move) && isTrump -> "kozir sarflanadi, lekin bosim shunga arziydi"
            Move.isAttack(move) && cheaper == 0 -> "qo'ldagi eng arzon karta"
            Move.isAttack(move) -> "arzonrog'i ($cheaper ta) saqlanadi, bu yurish kuchliroq"
            isTrump && cheaper == 0 -> "kozirsiz qoplab bo'lmaydi, eng pastini beradi"
            isTrump -> "kozir bilan qoplanadi, pastrog'i keyinga saqlanadi"
            cheaper == 0 -> "kozirni sarflamay, eng arzoni bilan qoplaydi"
            else -> "kozir saqlanadi"
        }
        return "$core | qo'lda $trumpsLeft kozir | $chance"
    }

    private fun value(view: DurakView, card: Int): Int {
        val r = DECK36.rank(card)
        return if (DECK36.suit(card) == view.trumpSuit) r + 20 else r
    }
}
