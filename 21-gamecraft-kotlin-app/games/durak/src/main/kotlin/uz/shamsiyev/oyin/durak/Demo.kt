package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*
import kotlin.random.Random

/** Tasodifiy holat yasab, maslahat qanday ko'rinishini ko'rsatadi. */
fun main() {
    val rng = Random(11)
    val advisor = DurakAdvisor()
    val state = DurakState.newGame(DurakRules(playerCount = 3), rng)
    val bots = List(3) { HeuristicBot() }

    var shown = 0
    var steps = 0
    while (state.phase != Phase.OVER && shown < 4 && steps++ < 400) {
        if (state.toMove == 0) {
            val view = state.toView(0)
            val advice = advisor.advise(view)
            println("─".repeat(58))
            println("kozir ${DECK36.suitNames[state.trumpSuit]} · zaxira ${state.deckLeft} · ${state.phase}")
            print("stol: ")
            for (i in 0 until state.tableCount) {
                print(DECK36.name(state.attacks[i]))
                if (state.defends[i] != NO_CARD) print("/${DECK36.name(state.defends[i])}")
                print("  ")
            }
            println()
            println("qo'lim: ${state.hands[0].render(DECK36)}")
            println("raqiblar: ${state.hands[1].count()} va ${state.hands[2].count()} karta")
            println()
            println("  >>> ${advice.headline.uppercase()}")
            println("      ${advice.reason}")
            advice.caveat?.let { println("      (!) $it") }
            shown++
        }
        val moves = state.legalMoves()
        if (moves.isEmpty()) break
        state.apply(bots[state.toMove].chooseMove(state, moves, state.toMove))
    }
    println("─".repeat(58))
}
