package uz.shamsiyev.oyin.durak

import uz.shamsiyev.oyin.core.*
import java.io.InputStream

/** O'rgatilgan shablonlar to'plami. Android'da assets'dan, kompyuterda fayldan o'qiladi. */
class DurakProfil(
    val rank: ShablonBanki,
    val suit: ShablonBanki,
    val raqam: ShablonBanki,
    val pufak: ShablonBanki,
) {
    companion object {
        /** [och] — fayl nomini oqimga aylantiradi (assets yoki disk). */
        fun oqi(och: (String) -> InputStream): DurakProfil {
            fun bank(nom: String): ShablonBanki {
                val nomlar = nomlarniOqi(och("$nom.names.json"))
                return ShablonBanki.oqi(och("$nom.bank"), nomlar)
            }
            return DurakProfil(bank("rank"), bank("suit"), bank("raqam"), bank("pufakcha"))
        }

        /** ["K","J",...] ko'rinishidagi sodda ro'yxat — kutubxona shart emas. */
        private fun nomlarniOqi(s: InputStream): List<String> {
            val matn = s.bufferedReader().use { it.readText() }
            return Regex("\"((?:[^\"\\\\]|\\\\.)*)\"").findAll(matn).map { it.groupValues[1] }.toList()
        }
    }
}

data class OqilganKarta(val karta: String?, val zona: String, val ishonch: Float, val quti: Bolak)

data class Hodisa(val kim: String, val hodisa: String, val ishonch: Float)

/** Bitta kadrdan o'qilgan hamma narsa. */
data class EkranHolati(
    val qol: List<String>,
    val stol: List<OqilganKarta>,
    val kozir: String?,
    val zaxira: Int?,
    val hodisalar: List<Hodisa>,
    val himoyachi: String?,
    val oqilmagan: Int,
    val beruBormi: Boolean = false,
    val faolOyinchi: String? = null,
)

class DurakKoz(private val profil: DurakProfil) {

    private val qizilMastlar = setOf("D", "H")
    private val qoraMastlar = setOf("S", "C")

    fun kartalar(f: Frame): List<OqilganKarta> {
        val natija = ArrayList<OqilganKarta>()

        // Kozir kartasi yonboshlab yotadi va alohida, burilgan holda o'qiladi.
        // Asosiy qidiruv o'sha hududga tegmasligi kerak — aks holda bitta karta
        // ikki marta, ustiga stol kartasi deb yoziladi.
        val asosiy = Koz.burchaklar(f).filter {
            !Koz.KOZIR_ROI.ichidami(it.quti.cx, it.quti.cy, f.width, f.height)
        }
        for (t in asosiy) natija.add(oqi(f, t, f.height, null))

        val kozir = Koz.kozirBurchagi(f)
        if (kozir != null) natija.add(oqi(kozir.second, kozir.first, kozir.second.height, "kozir"))

        return takrorniTozala(natija)
    }

    private fun oqi(src: Frame, t: Koz.Burchak, balandlik: Int, majburiyZona: String?): OqilganKarta {
        val ruxsat = if (t.rang == "qizil") qizilMastlar else qoraMastlar
        val r = profil.rank.tanla(namuna(src, t.rank.rect()))
        val s = profil.suit.tanla(namuna(src, t.suit.rect()), ruxsat)
        val ishonch = minOf(r.ball, s.ball)
        if (!ShablonBanki.qabul(r) || !ShablonBanki.qabul(s)) {
            return OqilganKarta(null, majburiyZona ?: "kadr", ishonch, t.quti)
        }
        val yc = t.quti.cy / balandlik
        val zona = majburiyZona ?: if (yc > 0.66) "qol" else "stol"
        return OqilganKarta(r.nom + s.nom, zona, ishonch, t.quti)
    }

    /**
     * Bitta karta ikki joyda bo'la olmaydi. Shunday bo'lsa — biri albatta xato.
     * Ishonchi pastrog'i "noma'lum" ga chiqariladi: maslahatchiga xato karta
     * berishdan ko'ra, bilmaslik xavfsiz.
     */
    private fun takrorniTozala(hammasi: List<OqilganKarta>): List<OqilganKarta> {
        val engYaxshi = HashMap<String, OqilganKarta>()
        for (k in hammasi) {
            val nom = k.karta ?: continue
            val oldingi = engYaxshi[nom]
            if (oldingi == null || k.ishonch > oldingi.ishonch) engYaxshi[nom] = k
        }
        return hammasi.map { if (it.karta != null && engYaxshi[it.karta] !== it) it.copy(karta = null) else it }
    }

    /** Zaxirada qolgan son. Raqam ko'rinmasa null — odatda zaxira tugagani. */
    fun zaxira(f: Frame, minBall: Float = 0.80f): Int? {
        val bolaklar = Koz.zaxiraBolaklari(f)
        if (bolaklar.isEmpty()) return null
        val sb = StringBuilder()
        for (b in bolaklar) {
            val t = profil.raqam.tanla(namuna(f, b.rect()))
            val nom = t.nom
            if (nom == null || t.ball < minBall) return null
            sb.append(nom)
        }
        return sb.toString().toIntOrNull()
    }

    fun hodisalar(f: Frame, minBall: Float = 0.80f): List<Hodisa> {
        val out = ArrayList<Hodisa>()
        for (c in Koz.pufakNomzodlari(f)) {
            val t = profil.pufak.tanla(namuna(f, c.matn.rect()))
            val nom = t.nom
            if (nom == null || nom == "?" || t.ball < minBall) continue
            out.add(Hodisa(c.kim, nom, t.ball))
        }
        return out
    }

    fun holat(f: Frame): EkranHolati {
        val ks = kartalar(f)
        return EkranHolati(
            qol = ks.filter { it.zona == "qol" && it.karta != null }.map { it.karta!! }.sorted(),
            stol = ks.filter { it.zona == "stol" && it.karta != null },
            kozir = ks.firstOrNull { it.zona == "kozir" }?.karta,
            zaxira = zaxira(f),
            hodisalar = hodisalar(f),
            himoyachi = Koz.himoyachi(f),
            oqilmagan = ks.count { it.karta == null },
            beruBormi = Koz.beruTugmasi(f),
            faolOyinchi = Koz.faolOyinchi(f),
        )
    }
}
