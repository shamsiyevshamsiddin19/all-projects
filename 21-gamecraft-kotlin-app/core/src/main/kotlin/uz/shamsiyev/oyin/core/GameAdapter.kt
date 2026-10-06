package uz.shamsiyev.oyin.core

/**
 * Yangi o'yin qo'shish = shu interfeysni amalga oshirish.
 * Android ilovasi faqat shu yerga qaraydi, o'yin qoidalarini bilmaydi.
 *
 * S — o'sha o'yinning holat turi (durakda qo'l/stol/kozir, boshqa o'yinda boshqa narsa).
 */
interface GameAdapter<S : Any> {
    /** Barqaror id, masalan "durak-rstgames". Sozlamalarda shu saqlanadi. */
    val id: String

    /** Foydalanuvchiga ko'rinadigan nom. */
    val title: String

    /** Qaysi Android ilovalarga tegishli (paket nomi). */
    val packageNames: Set<String>

    /** Kadrni o'qib holatga aylantiradi. [previous] — oldingi holat (kuzatuvni davom ettirish uchun). */
    fun observe(frame: Frame, previous: S?): Observation<S>

    /** Holatga qarab maslahat beradi. */
    fun advise(state: S): Advice
}

/**
 * Ekrandan o'qish natijasi.
 * [state] null bo'lsa — o'qib bo'lmadi, [problem] da sababi yoziladi.
 */
data class Observation<S>(
    val state: S?,
    val confidence: Double,
    val problem: String? = null,
)

/** Overlay oynasida ko'rsatiladigan maslahat. */
data class Advice(
    /** Asosiy gap: "♦8 ni tashla" */
    val headline: String,
    /** Bir qatorli sabab: "kozir emas, eng pasti" */
    val reason: String = "",
    val confidence: Double = 1.0,
    /** Ekranda nimani belgilash kerak (masalan qo'ldagi o'sha karta). */
    val highlight: List<Roi> = emptyList(),
    /** Ishonch past bo'lsa overlay buni ochiq yozadi. */
    val caveat: String? = null,
)
