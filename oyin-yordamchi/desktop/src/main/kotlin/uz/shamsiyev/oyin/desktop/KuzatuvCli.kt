package uz.shamsiyev.oyin.desktop

import uz.shamsiyev.oyin.durak.*
import java.io.File

/** Kadrlar ketma-ketligini kuzatib, o'yin jurnalini va oxirgi maslahatni chiqaradi. */
fun main(args: Array<String>) {
    val papka = File(args.getOrElse(0) { "data/frames/durak-3kishi-01" })
    val profilYon = File(args.getOrElse(1) { "games/durak/profil" })
    val chegara = args.getOrNull(2)?.toIntOrNull() ?: Int.MAX_VALUE

    val koz = DurakKoz(DurakProfil.oqi { nom -> File(profilYon, nom).inputStream() })
    val kuzatuv = Kuzatuv(raqiblarSoni = 2)

    val fayllar = papka.listFiles { f -> f.name.endsWith(".png") }!!.sorted().take(chegara)
    for (f in fayllar) {
        val raqam = f.nameWithoutExtension.removePrefix("f").toIntOrNull() ?: 0
        kuzatuv.qadam(koz.holat(rasmniOqi(f)), vaqt = raqam / 2.0)
    }

    println("=== O'YIN JURNALI ===")
    for (y in kuzatuv.jurnal) println("  %6.1fs  %s".format(y.vaqt, y.matn))

    val view = kuzatuv.dvigatelUchun()
    if (view == null) {
        println("\nkozir hali o'qilmadi")
        return
    }
    println("\n=== OXIRGI HOLAT ===")
    println("  kozir ${uz.shamsiyev.oyin.cards.DECK36.suitNames[view.trumpSuit]} · " +
            "zaxira ${view.deckLeft} · bitoda ${kuzatuv.bitoga.size} · " +
            "himoyachi ${kuzatuv.himoyachi ?: "-"}")
    println("  qo'lim: ${kuzatuv.qol.sorted().joinToString(" ")}")
    println("  stol: ${kuzatuv.juftlar.joinToString("  ") { it.hujum + (it.qoplagan?.let { d -> "/$d" } ?: "") }}")
    println("  raqiblarda jami: ${kuzatuv.raqiblardagiJami()}")

    val advice = DurakAdvisor().advise(view)
    println()
    println("  >>> ${advice.headline.uppercase()}")
    println("      ${advice.reason}")
    advice.caveat?.let { println("      (!) $it") }
}
