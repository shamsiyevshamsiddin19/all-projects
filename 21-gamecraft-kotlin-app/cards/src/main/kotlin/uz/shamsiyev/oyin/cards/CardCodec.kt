package uz.shamsiyev.oyin.cards

/**
 * Karta = oddiy butun son (0 dan taxlam hajmigacha): `rank * suitCount + suit`.
 * Shunday qilinganining sababi — millionlab variantni tez hisoblash kerak,
 * obyekt yaratish sekinlik qiladi.
 *
 * Taxlam ta'rifi almashtiriladi: 36 lik durak ham, 52 lik o'yin ham shu bilan ishlaydi.
 */
class CardCodec(val rankNames: List<String>, val suitNames: List<String>) {
    val rankCount = rankNames.size
    val suitCount = suitNames.size
    val size = rankCount * suitCount

    init {
        require(size <= 64) { "taxlam 64 kartadan oshmasligi kerak (CardSet 64 bitli)" }
    }

    fun card(rank: Int, suit: Int) = rank * suitCount + suit
    fun rank(card: Int) = card / suitCount
    fun suit(card: Int) = card % suitCount

    fun name(card: Int) = rankNames[rank(card)] + suitNames[suit(card)]

    /** "10♣" yoki "10C" ko'rinishidagi matnni kartaga aylantiradi. */
    fun parse(text: String): Int {
        val t = text.trim()
        val suitIndex = suitNames.indexOfFirst { t.endsWith(it) }
        require(suitIndex >= 0) { "mast topilmadi: $text" }
        val rankText = t.dropLast(suitNames[suitIndex].length)
        val rankIndex = rankNames.indexOf(rankText)
        require(rankIndex >= 0) { "daraja topilmadi: $text" }
        return card(rankIndex, suitIndex)
    }

    fun allCards(): IntArray = IntArray(size) { it }
}

/** Durak taxlami: 36 karta, past darajadan yuqoriga. */
val DECK36 = CardCodec(
    rankNames = listOf("6", "7", "8", "9", "10", "J", "Q", "K", "A"),
    suitNames = listOf("♠", "♣", "♦", "♥"),
)

/** To'liq 52 lik — keyinchalik boshqa o'yinlar uchun. */
val DECK52 = CardCodec(
    rankNames = listOf("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"),
    suitNames = listOf("♠", "♣", "♦", "♥"),
)
