package uz.shamsiyev.oyin.app

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
/**
 * Ikki ruxsat kerak: ekran ustida oyna ochish va ekranni o'qish.
 * Ikkalasini ham foydalanuvchi o'zi tasdiqlaydi; ilova hech narsani bosmaydi.
 */
class AsosiyOyna : Activity() {

    private companion object { const val EKRAN_SOROVI = 1 }

    private lateinit var holat: TextView
    private lateinit var tugma: Button

    override fun onActivityResult(soro: Int, kod: Int, malumot: Intent?) {
        super.onActivityResult(soro, kod, malumot)
        if (soro != EKRAN_SOROVI) return
        if (kod == RESULT_OK && malumot != null) {
            val xizmat = Intent(this, EkranXizmati::class.java).apply {
                putExtra(EkranXizmati.NATIJA_KODI, kod)
                putExtra(EkranXizmati.NATIJA_MALUMOT, malumot)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(xizmat)
            else startService(xizmat)
            holatniYangila("ishlayapti - o'yinni oching")
        } else {
            holatniYangila("ekranni o'qishga ruxsat berilmadi")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val dp = { v: Int -> (v * resources.displayMetrics.density).toInt() }

        holat = TextView(this).apply {
            textSize = 15f
            setPadding(0, dp(16), 0, dp(16))
        }
        tugma = Button(this).apply {
            text = "Boshlash"
            setOnClickListener { boshla() }
        }
        val toxtat = Button(this).apply {
            text = "To'xtatish"
            setOnClickListener {
                stopService(Intent(this@AsosiyOyna, EkranXizmati::class.java))
                holatniYangila("to'xtatildi")
            }
        }
        val izoh = TextView(this).apply {
            text = "Ilova o'yinga tegmaydi: hech narsani bosmaydi va o'zi yurmaydi — " +
                    "faqat ekranni o'qib, qaysi kartani yurishni aytadi.\n\n" +
                    "Eng aniq maslahat uchun o'yinni boshidan kuzatsin: bitoga ketgan " +
                    "kartalar ekranda ko'rinmaydi, ilova ularni eslab boradi."
            textSize = 13f
            setTextColor(Color.GRAY)
            setPadding(0, dp(24), 0, 0)
        }

        setContentView(LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(24), dp(48), dp(24), dp(24))
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
            addView(TextView(this@AsosiyOyna).apply {
                text = "O'yin yordamchisi"
                textSize = 22f
            })
            addView(holat)
            addView(tugma)
            addView(toxtat)
            addView(izoh)
        })

        holatniYangila("tayyor")
    }

    private fun holatniYangila(matn: String) {
        holat.text = matn
    }

    private fun boshla() {
        if (!Settings.canDrawOverlays(this)) {
            holatniYangila("ekran ustida oyna ochishga ruxsat kerak")
            startActivity(Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")))
            return
        }
        val mgr = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        @Suppress("DEPRECATION")
        startActivityForResult(mgr.createScreenCaptureIntent(), EKRAN_SOROVI)
    }
}
