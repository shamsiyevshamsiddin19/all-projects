package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.*
import kotlin.random.Random
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class RulesTest {

    private fun state(): DurakState = DurakState.newGame(DurakRules(playerCount = 3), Random(1))

    @Test
    fun `yuqori karta pastini qoplaydi`() {
        val s = state()
        val nonTrump = (0 until 4).first { it != s.trumpSuit }
        val six = DECK36.card(0, nonTrump)
        val nine = DECK36.card(3, nonTrump)
        assertTrue(s.beats(nine, six), "9 olti kartani qoplashi kerak")
        assertFalse(s.beats(six, nine), "6 to'qqizni qoplay olmaydi")
    }

    @Test
    fun `kozir boshqa mastni qoplaydi, teskarisi yo'q`() {
        val s = state()
        val nonTrump = (0 until 4).first { it != s.trumpSuit }
        val trumpSix = DECK36.card(0, s.trumpSuit)
        val aceOther = DECK36.card(8, nonTrump)
        assertTrue(s.beats(trumpSix, aceOther), "eng past kozir begona tuzni qoplaydi")
        assertFalse(s.beats(aceOther, trumpSix), "begona tuz kozirni qoplay olmaydi")
    }

    @Test
    fun `boshqa mast qoplay olmaydi`() {
        val s = state()
        val suits = (0 until 4).filter { it != s.trumpSuit }
        assertFalse(s.beats(DECK36.card(8, suits[0]), DECK36.card(0, suits[1])))
    }

    @Test
    fun `turni ochishda pas aytib bo'lmaydi`() {
        val s = state()
        assertEquals(Phase.ATTACK, s.phase)
        assertEquals(0, s.tableCount)
        assertFalse(s.legalMoves().any { it == Move.PASS }, "stol bo'sh - hujumchi turni ochishi shart")
    }

    @Test
    fun `qo'shib tashlash faqat stoldagi daraja bilan`() {
        val s = state()
        val first = s.legalMoves().first { Move.isAttack(it) }
        val rank = DECK36.rank(Move.card(first))
        s.apply(first)

        // Himoyachi qoplaydi yoki oladi - qoplasin, keyin qo'shimcha hujumni tekshiramiz.
        val defence = s.legalMoves().firstOrNull { Move.isDefend(it) } ?: return
        val defenceRank = DECK36.rank(Move.card(defence))
        s.apply(defence)

        if (s.phase != Phase.ATTACK) return
        for (m in s.legalMoves()) {
            if (!Move.isAttack(m)) continue
            val r = DECK36.rank(Move.card(m))
            assertTrue(r == rank || r == defenceRank, "stolda yo'q daraja bilan hujum qilib bo'lmaydi")
        }
    }

    @Test
    fun `bito bo'lsa himoyachi keyingi hujumchi bo'ladi`() {
        val s = state()
        val defenderBefore = s.defender
        var guard = 0
        while (s.attacker == (defenderBefore + 0) % 3 || true) {
            if (s.phase == Phase.OVER) return
            val moves = s.legalMoves()
            // himoyachi doim qoplasin, hujumchilar bir martadan keyin pas aytsin
            val m = when {
                s.phase == Phase.DEFEND -> moves.firstOrNull { Move.isDefend(it) } ?: return
                s.tableCount == 0 -> moves.first { Move.isAttack(it) }
                else -> Move.PASS
            }
            s.apply(m)
            if (s.tableCount == 0 && s.phase == Phase.ATTACK) break
            if (++guard > 50) return
        }
        assertEquals(defenderBefore, s.attacker, "bitodan keyin himoyachi hujum qiladi")
    }

    @Test
    fun `kartalar yo'qolmaydi va takrorlanmaydi`() {
        val rng = Random(7)
        repeat(200) {
            val bots = List(3) { RandomBot(rng) }
            playGame(bots, DurakRules(playerCount = 3), rng, check = true)
        }
    }

    @Test
    fun `har xil o'yinchi sonida o'yin tugaydi`() {
        for (players in 2..6) {
            val rng = Random(players.toLong())
            repeat(100) {
                val durak = playGame(List(players) { RandomBot(rng) }, DurakRules(playerCount = players), rng)
                assertTrue(durak in -1 until players, "noto'g'ri natija: $durak")
            }
        }
    }
}
