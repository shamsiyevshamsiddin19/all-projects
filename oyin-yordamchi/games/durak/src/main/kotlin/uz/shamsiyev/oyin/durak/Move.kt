package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.cards.CardCodec

/**
 * Yurish ham oddiy butun son bilan belgilanadi — tez bo'lishi uchun.
 *   0        = pas (qo'shib tashlamayman / bito)
 *   1        = olaman
 *   2..65    = hujum qilaman (karta)
 *   66..129  = qoplayman (karta)
 */
object Move {
    const val PASS = 0
    const val TAKE = 1
    const val ATTACK_BASE = 2
    const val DEFEND_BASE = 66

    fun attack(card: Int) = ATTACK_BASE + card
    fun defend(card: Int) = DEFEND_BASE + card

    fun isAttack(m: Int) = m in ATTACK_BASE until DEFEND_BASE
    fun isDefend(m: Int) = m >= DEFEND_BASE
    fun card(m: Int) = if (isDefend(m)) m - DEFEND_BASE else m - ATTACK_BASE

    fun name(m: Int, codec: CardCodec): String = when {
        m == PASS -> "pas"
        m == TAKE -> "olaman"
        isAttack(m) -> "hujum ${codec.name(card(m))}"
        else -> "qoplash ${codec.name(card(m))}"
    }
}
