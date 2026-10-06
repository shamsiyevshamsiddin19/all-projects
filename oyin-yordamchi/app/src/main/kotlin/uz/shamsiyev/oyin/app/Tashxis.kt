package uz.shamsiyev.oyin.app

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import uz.shamsiyev.oyin.core.Frame
import java.io.File
import java.io.OutputStream

/**
 * Tashxis: ilova ko'rgan xom kadrni va o'qigan natijasini telefonga saqlaydi.
 *
 * Nega kerak: telefonda jurnalga kirish imkoni bo'lmasa, nega ishlamayotganini
 * bilishning yagona yo'li - ilova nimani ko'rganini ko'rish. Xom kadr saqlansa,
 * uni kompyuterda o'sha tanish quvuridan o'tkazib, xatoni aniq topish mumkin.
 *
 * Fayllar `Download/oyin-yordamchi/` ichiga tushadi - u yerdan ulashish oson.
 */
class Tashxis(
    private val context: Context,
    private val nechta: Int = 4,
    /** Ilova ishga tushgach o'yin ochilishiga vaqt beriladi. */
    private val kechikishMs: Long = 12000,
) {

    private val boshlandi = android.os.SystemClock.uptimeMillis()
    private var saqlangan = 0
    private var oxirgiVaqt = 0L

    val tugadimi: Boolean get() = saqlangan >= nechta

    /** Kadrni va o'qilgan natijani saqlaydi. Kamida [oraliqMs] oralab. */
    fun saqla(kadr: Frame, izoh: String, oraliqMs: Long = 5000): Boolean {
        if (tugadimi) return false
        val hozir = android.os.SystemClock.uptimeMillis()
        if (hozir - boshlandi < kechikishMs) return false
        if (hozir - oxirgiVaqt < oraliqMs) return false
        oxirgiVaqt = hozir
        saqlangan++

        return try {
            val nom = "kadr-$saqlangan"
            yoz("$nom.png", "image/png") { oqim ->
                rasmga(kadr).compress(Bitmap.CompressFormat.PNG, 100, oqim)
            }
            yoz("$nom.txt", "text/plain") { oqim ->
                oqim.write(("o'lcham: ${kadr.width}x${kadr.height}\n$izoh\n").toByteArray())
            }
            true
        } catch (e: Throwable) {
            Log.e("OyinYordamchi", "tashxis saqlanmadi", e)
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
