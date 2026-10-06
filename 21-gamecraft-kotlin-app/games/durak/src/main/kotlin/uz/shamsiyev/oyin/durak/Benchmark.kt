package uz.shamsiyev.oyin.durak

import kotlin.random.Random

/**
 * Monte-Carlo bot qoidali botni yengadimi — Qadam 2 ning asosiy o'lchovi.
 * O'lchov: durak bo'lish foizi. Teng botlarda 2 kishilikda 50%, 3 kishilikda 33%.
 */
fun main(args: Array<String>) {
    val games = args.getOrNull(0)?.toIntOrNull() ?: 300
    val players = args.getOrNull(1)?.toIntOrNull() ?: 2
    val samples = args.getOrNull(2)?.toIntOrNull() ?: 60

    val rng = Random(2026)
    val rules = DurakRules(playerCount = players)

    // 0-o'rin Monte-Carlo, qolganlari qoidali bot.
    val bots = List(players) { i ->
        if (i == 0) PimcBot(samples = samples, rng = rng, budgetMillis = 2000) else HeuristicBot()
    }

    println("Sinov: $games o'yin, $players o'yinchi, $samples taxmin")
    println("0-o'rin = monte-carlo, qolgani = qoidali bot")

    val durakCount = IntArray(players)
    var draws = 0
    val started = System.currentTimeMillis()

    repeat(games) { g ->
        val durak = playGame(bots, rules, rng, check = false)
        if (durak < 0) draws++ else durakCount[durak]++
        if ((g + 1) % 50 == 0) {
            val rate = durakCount[0] * 100.0 / (g + 1)
            println("  ${g + 1} o'yin: monte-carlo durak bo'ldi ${"%.1f".format(rate)}%")
        }
    }

    val ms = System.currentTimeMillis() - started
    val expected = 100.0 / players
    val mc = durakCount[0] * 100.0 / games
    println()
    println("Vaqt: ${ms / 1000}s, bitta yurish o'rtacha ~${ms / games} ms/o'yin")
    println("Durrang: $draws")
    println("Monte-Carlo durak bo'ldi: ${"%.1f".format(mc)}% (teng bo'lsa ${"%.1f".format(expected)}%)")
    for (p in 1 until players) {
        println("  qoidali bot $p: ${"%.1f".format(durakCount[p] * 100.0 / games)}%")
    }
    val winRate = 100.0 - mc
    println("=> Monte-Carlo yutuq darajasi: ${"%.1f".format(winRate)}%")
}
