package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*
import kotlin.random.Random

/**
 * Bitta o'yinni oxirigacha o'ynaydi va durak bo'lgan o'yinchini qaytaradi (-1 = durrang).
 * Har yurishda qoidalar buzilmaganini tekshiradi — xato bo'lsa darhol ko'rinadi.
 */
fun playGame(bots: List<DurakBot>, rules: DurakRules, rng: Random, check: Boolean = true): Int {
    val state = DurakState.newGame(rules, rng)
    var steps = 0
    while (state.phase != Phase.OVER) {
        if (check) verify(state)
        val moves = state.legalMoves()
        check(moves.isNotEmpty()) { "yurish yo'q, lekin o'yin tugamagan:\n$state" }
        val move = bots[state.toMove].chooseMove(state, moves, state.toMove)
        check(moves.any { it == move }) { "bot noqonuniy yurish qildi: $move" }
        state.apply(move)
        check(++steps < 2000) { "o'yin tugamadi — qoidada tsikl bor:\n$state" }
    }
    return state.durak
}

/** Kartalar yo'qolmaganini va takrorlanmaganini tekshiradi. */
fun verify(state: DurakState) {
    var seen = EMPTY_CARDS
    var total = 0
    fun add(c: Int) {
        check(!seen.has(c)) { "karta ikki joyda: ${DECK36.name(c)}" }
        seen = seen.with(c); total++
    }
    for (h in state.hands) h.forEachCard { add(it) }
    state.discard.forEachCard { add(it) }
    for (i in state.deckPos until state.deck.size) add(state.deck[i])
    for (i in 0 until state.tableCount) {
        add(state.attacks[i])
        if (state.defends[i] != NO_CARD) add(state.defends[i])
    }
    check(total == DECK36.size) { "kartalar soni $total, 36 bo'lishi kerak:\n$state" }
}

fun main(args: Array<String>) {
    val games = args.getOrNull(0)?.toIntOrNull() ?: 10_000
    val players = args.getOrNull(1)?.toIntOrNull() ?: 3
    val rules = DurakRules(playerCount = players)
    val rng = Random(42)

    println("Durak qoidalari sinovi: $games o'yin, $players o'yinchi")

    val bots = List(players) { HeuristicBot() }
    val durakCount = IntArray(players)
    var draws = 0
    val started = System.currentTimeMillis()

    repeat(games) {
        val durak = playGame(bots, rules, rng)
        if (durak < 0) draws++ else durakCount[durak]++
    }

    val ms = System.currentTimeMillis() - started
    println("Tugadi: ${ms} ms (${"%.0f".format(games * 1000.0 / ms)} o'yin/sek)")
    println("Durrang: $draws")
    for (p in 0 until players) {
        println("  o'yinchi $p durak bo'ldi: ${durakCount[p]} (${"%.1f".format(durakCount[p] * 100.0 / games)}%)")
    }
}
