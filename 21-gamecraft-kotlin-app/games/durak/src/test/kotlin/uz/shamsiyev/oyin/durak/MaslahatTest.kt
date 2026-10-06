package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.core.Bolak
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/**
 * Maslahat qachon BERILMASLIGI kerakligi haqida.
 *
 * Ikkisi ham haqiqiy o'yinda chiqqan xato: biri bezovta qiladi, ikkinchisi
 * o'yinni boy beradi. Shuning uchun sinov ekrandan o'qilgan holatdan boshlanadi
 * va butun zanjirni (kuzatuv -> ko'rinish -> maslahat) o'tadi.
 */
class MaslahatTest {

    private fun stolKartasi(nom: String, x: Int) =
        OqilganKarta(nom, "stol", 1.0f, Bolak(x, 300, 40, 56, 2240))

    private fun holat(
        qol: List<String>,
        stol: List<OqilganKarta> = emptyList(),
        himoyachi: String? = null,
        beruBormi: Boolean = false,
        faolOyinchi: String? = null,
    ) = EkranHolati(
        qol = qol,
        stol = stol,
        kozir = "8C",
        zaxira = 10,
        hodisalar = emptyList(),
        himoyachi = himoyachi,
        oqilmagan = 0,
        beruBormi = beruBormi,
        faolOyinchi = faolOyinchi,
    )

    private val qolim = listOf("6S", "9D", "JH", "QS", "KD", "AH")

    @Test
    fun `raqiblar bir-biriga o'ynayotganda maslahat berilmaydi`() {
        val k = Kuzatuv(raqiblarSoni = 2)
        k.qadam(holat(qolim, stol = listOf(stolKartasi("7D", 400)), himoyachi = "ong", faolOyinchi = "chap"))
        val view = k.dvigatelUchun()!!

        assertTrue(view.toMove != view.me, "navbat o'ng raqibda bo'lishi kerak")
        assertEquals("navbat sizda emas", DurakAdvisor().advise(view).headline)
    }

    @Test
    fun `himoyachiman-u stol ko'rinmasa maslahat berilmaydi`() {
        val k = Kuzatuv(raqiblarSoni = 2)
        // "I take" tugmasi ko'rinadi (himoyachi menman), lekin stolda birorta
        // karta o'qilmagan. Avval dvigatel shu yerda "ol" deb chiqarardi.
        k.qadam(holat(qolim, stol = emptyList(), beruBormi = true, faolOyinchi = "men"))
        val view = k.dvigatelUchun()!!

        assertEquals(view.me, view.defender, "himoyachi men bo'lishim kerak")
        assertEquals(0, view.undefendedCount())
        val maslahat = DurakAdvisor().advise(view)
        assertEquals("maslahat yo'q", maslahat.headline)
        assertTrue(!maslahat.headline.startsWith("ol"), "stol ko'rinmasa 'ol' deyilmaydi")
    }

    @Test
    fun `haqiqiy himoyada maslahat baribir beriladi`() {
        val k = Kuzatuv(raqiblarSoni = 2)
        k.qadam(holat(qolim, stol = listOf(stolKartasi("7D", 400)), beruBormi = true, faolOyinchi = "men"))
        val view = k.dvigatelUchun()!!

        assertEquals(view.me, view.toMove)
        assertEquals(1, view.undefendedCount())
        val bosh = DurakAdvisor().advise(view).headline
        assertTrue(bosh !in setOf("maslahat yo'q", "navbat sizda emas", "kutilmoqda"),
            "qoplanmagan karta bor - maslahat kutilgan, lekin: $bosh")
    }
}
