package uz.shamsiyev.oyin.desktop

import uz.shamsiyev.oyin.core.Frame
import uz.shamsiyev.oyin.durak.DurakKoz
import uz.shamsiyev.oyin.durak.DurakProfil
import java.awt.image.BufferedImage
import java.io.File
import javax.imageio.ImageIO

/** PNG ni Frame ga aylantiradi — faqat kompyuterda; Android'da Bitmap ishlatiladi. */
fun rasmniOqi(fayl: File): Frame {
    val img: BufferedImage = ImageIO.read(fayl)
    val w = img.width
    val h = img.height
    val px = IntArray(w * h)
    img.getRGB(0, 0, w, h, px, 0, w)
    for (i in px.indices) px[i] = px[i] and 0xFFFFFF
    return Frame(w, h, px)
}

private fun profilniOqi(yon: File) = DurakProfil.oqi { nom -> File(yon, nom).inputStream() }

fun main(args: Array<String>) {
    val yol = File(args.getOrElse(0) { "data/frames/durak-3kishi-01" })
    val profilYon = File(args.getOrElse(1) { "games/durak/profil" })
    val koz = DurakKoz(profilniOqi(profilYon))

    val fayllar = if (yol.isDirectory) yol.listFiles { f -> f.name.endsWith(".png") }!!.sorted()
    else listOf(yol)

    val tafsil = args.any { it == "tafsil" }

    for (f in fayllar) {
        val kadr = rasmniOqi(f)
        if (tafsil) {
            for (t in uz.shamsiyev.oyin.durak.Koz.burchaklar(kadr)) {
                println("  burchak ${t.rang} quti=(${t.quti.x},${t.quti.y},${t.quti.w},${t.quti.h}) " +
                        "rank=(${t.rank.x},${t.rank.y},${t.rank.w},${t.rank.h}) " +
                        "mast=(${t.suit.x},${t.suit.y},${t.suit.w},${t.suit.h}) oqlik=${"%.2f".format(t.oqlik)}")
            }
        }
        val h = koz.holat(kadr)
        val stol = h.stol.mapNotNull { it.karta }.sorted()
        val hodisa = if (h.hodisalar.isEmpty()) "" else
            " | hodisa: " + h.hodisalar.joinToString(", ") { "${it.kim}=${it.hodisa}" }
        println("${f.name}: qo'l: ${h.qol.joinToString(" ").ifEmpty { "-" }} | " +
                "stol: ${stol.joinToString(" ").ifEmpty { "-" }} | " +
                "kozir: ${h.kozir ?: "-"} | zaxira: ${h.zaxira ?: "-"} | " +
                "himoyachi: ${h.himoyachi ?: "-"}$hodisa")
    }
}
