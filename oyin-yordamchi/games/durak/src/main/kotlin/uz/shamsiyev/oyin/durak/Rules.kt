package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*

/**
 * Shu holatda mumkin bo'lgan barcha yurishlar.
 *
 * Model soddalashtirilgan va Rstgames oqimiga mos: stolda bir vaqtda
 * faqat bitta qoplanmagan karta turadi — kimdir tashlaydi, himoyachi javob beradi.
 */
fun DurakState.legalMoves(): IntArray {
    if (phase == Phase.OVER) return IntArray(0)
    val moves = ArrayList<Int>(16)

    when (phase) {
        Phase.DEFEND -> {
            moves.add(Move.TAKE)
            val idx = undefendedIndex()
            if (idx >= 0) {
                val atk = attacks[idx]
                hands[toMove].forEachCard { c -> if (beats(c, atk)) moves.add(Move.defend(c)) }
            }
        }

        Phase.ATTACK, Phase.THROW_IN -> {
            // Stol bo'sh bo'lsa hujumchi pas aytolmaydi — turni ochishi shart.
            if (tableCount > 0) moves.add(Move.PASS)
            if (tableCount < boutLimit) {
                if (tableCount == 0) {
                    hands[toMove].forEachCard { c -> moves.add(Move.attack(c)) }
                } else {
                    val ranks = ranksOnTable()
                    hands[toMove].forEachCard { c ->
                        if ((ranks ushr DECK36.rank(c)) and 1 == 1) moves.add(Move.attack(c))
                    }
                }
            }
        }

        Phase.OVER -> {}
    }
    return moves.toIntArray()
}

/** Yurishni bajaradi va holatni o'zgartiradi. */
fun DurakState.apply(move: Int) {
    when {
        move == Move.PASS -> applyPass()
        move == Move.TAKE -> applyTake()
        Move.isAttack(move) -> applyAttack(Move.card(move))
        else -> applyDefend(Move.card(move))
    }
}

private fun DurakState.applyAttack(card: Int) {
    hands[toMove] = hands[toMove].without(card)
    attacks[tableCount] = card
    defends[tableCount] = NO_CARD
    tableCount++

    if (phase == Phase.THROW_IN) {
        // Himoyachi allaqachon olgan — qoplash bo'lmaydi, faqat qo'shib tashlash davom etadi.
        resetPassed()
        advanceThrower()
        if (allPassed()) endBout(defender)
    } else {
        resetPassed()
        phase = Phase.DEFEND
        toMove = defender
    }
}

private fun DurakState.applyDefend(card: Int) {
    hands[toMove] = hands[toMove].without(card)
    val idx = undefendedIndex()
    defends[idx] = card

    // Stol to'ldi yoki himoyachining kartasi tugadi — tur tugaydi (bito).
    if (tableCount >= boutLimit || hands[defender].isEmpty()) {
        endBout(null)
        return
    }
    phase = Phase.ATTACK
    resetPassed()
    toMove = attacker
    if (passed[toMove]) advanceThrower()
    if (allPassed()) endBout(null)
}

private fun DurakState.applyTake() {
    if (!rules.throwInAfterTake) {
        endBout(defender)
        return
    }
    phase = Phase.THROW_IN
    resetPassed()
    toMove = attacker
    if (passed[toMove]) advanceThrower()
    if (allPassed()) endBout(defender)
}

private fun DurakState.applyPass() {
    passed[toMove] = true
    if (allPassed()) {
        endBout(if (phase == Phase.THROW_IN) defender else null)
    } else {
        advanceThrower()
    }
}

/** Qo'shib tashlashi mumkin bo'lganlar belgilanadi; qolganlari "pas qilgan" hisoblanadi. */
private fun DurakState.resetPassed() {
    for (p in passed.indices) {
        passed[p] = out[p] || p == defender || hands[p].isEmpty() || tableCount >= boutLimit
    }
}

private fun DurakState.allPassed(): Boolean = passed.all { it }

private fun DurakState.advanceThrower() {
    var p = (toMove + 1) % rules.playerCount
    repeat(rules.playerCount) {
        if (!passed[p]) { toMove = p; return }
        p = (p + 1) % rules.playerCount
    }
}

/** Keyingi o'yinda qatnashayotgan o'yinchi (shu o'rindan keyin). */
private fun DurakState.nextActive(from: Int): Int {
    var p = (from + 1) % rules.playerCount
    repeat(rules.playerCount) {
        if (!out[p]) return p
        p = (p + 1) % rules.playerCount
    }
    return from
}

/**
 * Tur tugadi. [takenBy] null bo'lsa — bito (stol bitoga ketadi),
 * aks holda himoyachi hamma kartani qo'liga oladi.
 */
private fun DurakState.endBout(takenBy: Int?) {
    val boutAttacker = attacker
    val boutDefender = defender

    for (i in 0 until tableCount) {
        val a = attacks[i]
        val d = defends[i]
        if (takenBy == null) {
            discard = discard.with(a)
            if (d != NO_CARD) discard = discard.with(d)
        } else {
            hands[takenBy] = hands[takenBy].with(a)
            if (d != NO_CARD) hands[takenBy] = hands[takenBy].with(d)
        }
        attacks[i] = NO_CARD
        defends[i] = NO_CARD
    }
    tableCount = 0

    refill(boutAttacker, boutDefender)

    if (deckPos >= deck.size) {
        for (p in 0 until rules.playerCount) if (hands[p].isEmpty()) out[p] = true
    }

    val remaining = (0 until rules.playerCount).filter { !out[it] }
    if (remaining.size <= 1) {
        durak = remaining.firstOrNull() ?: NO_CARD
        phase = Phase.OVER
        return
    }

    // Bito bo'lsa — himoyachi keyingi hujumchi. Olgan bo'lsa — undan keyingisi.
    attacker = if (takenBy == null && !out[boutDefender]) boutDefender else nextActive(boutDefender)
    defender = nextActive(attacker)
    toMove = attacker
    phase = Phase.ATTACK
    boutLimit = minOf(rules.maxAttacks, hands[defender].count())
    resetPassed()
}

/** Zaxiradan karta olish: avval hujumchi, keyin navbat bo'yicha, himoyachi eng oxirida. */
private fun DurakState.refill(boutAttacker: Int, boutDefender: Int) {
    val order = ArrayList<Int>(rules.playerCount)
    var p = boutAttacker
    repeat(rules.playerCount) {
        if (p != boutDefender) order.add(p)
        p = (p + 1) % rules.playerCount
    }
    order.add(boutDefender)

    for (q in order) {
        while (hands[q].count() < rules.handSize && deckPos < deck.size) {
            hands[q] = hands[q].with(deck[deckPos++])
        }
    }
}
