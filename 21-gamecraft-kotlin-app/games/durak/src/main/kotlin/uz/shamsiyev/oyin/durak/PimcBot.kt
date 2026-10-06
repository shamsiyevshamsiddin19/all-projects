package uz.shamsiyev.oyin.durak

import kotlin.random.Random

/**
 * Monte-Carlo: raqib qo'lini noma'lum kartalardan ko'p marta taxmin qiladi,
 * har taxminda har bir yurishni o'ynab ko'radi va o'rtacha eng yaxshisini tanlaydi.
 *
 * Zaxira tugab, kartalar kamayganda taxminlar soni kamayadi va natija
 * amalda mukammal o'yinga yaqinlashadi.
 */
class PimcBot(
    private val samples: Int = 120,
    private val rollout: DurakBot = HeuristicBot(),
    private val rng: Random = Random.Default,
    /** Shu vaqtdan oshsa, hisobni to'xtatib bor natijani beradi (telefon uchun). */
    private val budgetMillis: Long = 400,
) : DurakBot {
    override val name = "monte-carlo($samples)"

    override fun chooseMove(state: DurakState, moves: IntArray, me: Int): Int {
        if (moves.size == 1) return moves[0]

        val view = state.toView(me)
        val score = DoubleArray(moves.size)
        val deadline = System.currentTimeMillis() + budgetMillis
        var done = 0

        for (s in 0 until samples) {
            val sampled = view.sample(rng)
            for (i in moves.indices) {
                val child = sampled.copy()
                child.apply(moves[i])
                score[i] += playout(child, me)
            }
            done++
            if (System.currentTimeMillis() > deadline) break
        }

        var best = 0
        for (i in moves.indices) if (score[i] > score[best]) best = i
        return moves[best]
    }

    /** Natija: durak bo'lmaslik = 1.0, durrang = 0.5, durak = 0.0 */
    private fun playout(state: DurakState, me: Int): Double {
        var steps = 0
        while (state.phase != Phase.OVER && steps++ < 500) {
            val moves = state.legalMoves()
            if (moves.isEmpty()) break
            state.apply(rollout.chooseMove(state, moves, state.toMove))
        }
        return when (state.durak) {
            me -> 0.0
            NO_CARD -> 0.5
            else -> 1.0
        }
    }

    /** Maslahat uchun: har bir yurishning bahosi bilan birga qaytaradi. */
    fun rank(view: DurakView, moves: IntArray): List<Pair<Int, Double>> {
        val score = DoubleArray(moves.size)
        val deadline = System.currentTimeMillis() + budgetMillis
        var used = 0
        for (s in 0 until samples) {
            val sampled = view.sample(rng)
            for (i in moves.indices) {
                val child = sampled.copy()
                child.apply(moves[i])
                score[i] += playout(child, view.me)
            }
            used++
            if (System.currentTimeMillis() > deadline) break
        }
        val n = used.coerceAtLeast(1).toDouble()
        return moves.indices.map { moves[it] to score[it] / n }.sortedByDescending { it.second }
    }
}
