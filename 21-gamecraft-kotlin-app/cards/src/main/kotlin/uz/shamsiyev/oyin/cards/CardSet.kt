package uz.shamsiyev.oyin.cards

/**
 * Karta to'plami — 64 bitli son, har bit bitta karta.
 * Qo'shish/olib tashlash/tekshirish bitta protsessor amali, shuning uchun juda tez.
 */
typealias CardSet = Long

const val EMPTY_CARDS: CardSet = 0L

inline fun CardSet.has(card: Int): Boolean = (this ushr card) and 1L == 1L
inline fun CardSet.with(card: Int): CardSet = this or (1L shl card)
inline fun CardSet.without(card: Int): CardSet = this and (1L shl card).inv()
inline fun CardSet.count(): Int = java.lang.Long.bitCount(this)
inline fun CardSet.isEmpty(): Boolean = this == 0L

/** To'plamdagi har bir karta ustida yurish. */
inline fun CardSet.forEachCard(action: (Int) -> Unit) {
    var m = this
    while (m != 0L) {
        action(java.lang.Long.numberOfTrailingZeros(m))
        m = m and (m - 1L)
    }
}

fun CardSet.toList(): List<Int> {
    val out = ArrayList<Int>(count())
    forEachCard { out.add(it) }
    return out
}

fun cardSetOf(vararg cards: Int): CardSet {
    var s = EMPTY_CARDS
    for (c in cards) s = s.with(c)
    return s
}

fun CardSet.render(codec: CardCodec): String =
    toList().sorted().joinToString(" ") { codec.name(it) }
