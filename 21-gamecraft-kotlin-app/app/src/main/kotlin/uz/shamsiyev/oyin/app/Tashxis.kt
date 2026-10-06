package uz.shamsiyev.oyin.app

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import uz.shamsiyev.oyin.core.Frame
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.OutputStream

/**
 * Tashxis: ilova ko'rgan xom kadrni va o'qigan natijasini chiqaradi.
 *
 * Nega kerak: telefonda jurnalga kirish imkoni bo'lmasa, nega ishlamayotganini
 * bilishning yagona ishonchli yo'li - ilova nimani ko'rganini ko'rish. Xom kadr
 * bo'lsa, uni kompyuterdagi o'sha tanish quvuridan o'tkazib, xato qaysi
 * bosqichda ekanini aniq topish mumkin.
 *
 * Avval serverga yuboriladi (foydalanuvchidan hech narsa talab qilmaydi).
 * Yuborib bo'lmasa - `Download/oyin-yordamchi/` ichiga saqlanadi.
 */
class Tashxis(
    private val context: Context,
    private val yuboruvchi: Yuboruvchi? = null,
    private val nechta: Int = 12,
    /** Ilova ishga tushgach o'yin ochilishiga vaqt beriladi. */
    private val kechikishMs: Long = 12000,
) {

    private val boshlandi = android.os.SystemClock.uptimeMillis()
    private var saqlangan = 0
    private var oxirgiVaqt = 0L

    /** Oxirgi kadr qayerga ketgani - overlay shuni ko'rsatadi. */
    var oxirgiNatija: String = ""
        private set

    val tugadimi: Boolean get() = saqlangan >= nechta

    /** Kadrni va o'qilgan natijani chiqaradi. Kamida [oraliqMs] oralab. */
    fun saqla(kadr: Frame, izoh: String, oraliqMs: Long = 5000): Boolean {
        if (tugadimi) return false
        val hozir = android.os.SystemClock.uptimeMillis()
        if (hozir - boshlandi < kechikishMs) return false
        if (hozir - oxirgiVaqt < oraliqMs) return false
        oxirgiVaqt = hozir
        saqlangan++

        return try {
            val nom = "kadr-%02d".format(saqlangan)
            val rasm = ByteArrayOutputStream().also {
                rasmga(kadr).compress(Bitmap.CompressFormat.PNG, 100, it)
            }.toByteArray()
            val matn = "o'lcham: ${kadr.width}x${kadr.height}\n$izoh\n".toByteArray()

            val yuborildi = yuboruvchi != null &&
                    yuboruvchi.yubor("$nom.png", rasm, "image/png") &&
                    yuboruvchi.yubor("$nom.txt", matn, "text/plain")

            if (!yuborildi) {
                yoz("$nom.png", "image/png") { it.write(rasm) }
                yoz("$nom.txt", "text/plain") { it.write(matn) }
            }
            oxirgiNatija = if (yuborildi) "yuborildi $saqlangan/$nechta"
            else "telefonga saqlandi $saqlangan/$nechta"
            true
        } catch (e: Throwable) {
            Log.e("OyinYordamchi", "tashxis chiqmadi", e)
            oxirgiNatija = "tashxis chiqmadi"
            false
        }
    }

    private fun rasmga(kadr: Frame): Bitmap {
        // Frame'da shaffoflik yo'q (0x00RRGGBB), Bitmap uchun to'ldirish kerak.
        val px = IntArray(kadr.pixels.size) { kadr.pixels[it] or 0xFF000000.toInt() }
        return Bitmap.createBitmap(px, kadr.width, kadr.height, Bitmap.Config.ARGB_8888)
    }

    private inline fun yoz(nom: String, turi: String, yozuvchi: (OutputStream) -> Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val qiymatlar = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, nom)
                put(MediaStore.Downloads.MIME_TYPE, turi)
                put(MediaStore.Downloads.RELATIVE_PATH, "Download/oyin-yordamchi")
            }
            val uri = context.contentResolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI, qiymatlar
            ) ?: error("Download papkasiga yozib bo'lmadi")
            context.contentResolver.openOutputStream(uri)!!.use(yozuvchi)
        } else {
            val papka = File(
                Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),
                "oyin-yordamchi"
            ).apply { mkdirs() }
            File(papka, nom).outputStream().use(yozuvchi)
        }
    }
}
