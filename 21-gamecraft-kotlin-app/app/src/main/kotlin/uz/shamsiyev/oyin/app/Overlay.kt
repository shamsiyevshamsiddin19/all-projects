package uz.shamsiyev.oyin.app

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.util.TypedValue
import android.view.Gravity
import android.view.WindowManager
import android.widget.LinearLayout
import android.widget.TextView

/**
 * O'yin ustida turadigan kichik oyna.
 *
 * Bosishlarni o'tkazib yuboradi (FLAG_NOT_TOUCHABLE) - ya'ni o'yinni bloklamaydi
 * va hech narsani bosmaydi. Faqat qaraydi va aytadi.
 *
 * Eng muhimi: oynaga FLAG_SECURE qo'yiladi. Ekranni o'qish (MediaProjection)
 * xavfsiz oynalarni tushirmaydi, ya'ni ilova O'Z OYNASINI ko'rmaydi. Busiz
 * overlay ostidagi hamma narsa ilovadan yashirin qoladi: haqiqiy o'yinda u
 * chap raqibning avatarini yopib, "kim himoyada" belgisini o'ldirgan edi.
 *
 * Joyi ham tasodifiy emas: 99 ta haqiqiy kadrda karta qayerda paydo bo'lgani
 * o'lchanib, o'qiladigan hududlarga tegmaydigan eng bo'sh to'rtburchak
 * tanlangan. FLAG_SECURE ishlamagan qurilmada zarari shu bilan kamayadi.
 */
class Overlay(private val context: Context) {

    companion object {
        /** O'lchangan eng bo'sh joy: o'ng tomonda, raqib avatari ostida. */
        private const val CHAP = 0.597
        private const val TEPA = 0.169
        private const val ENI = 0.40
    }

    private val wm = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var qavat: LinearLayout? = null
    private lateinit var sarlavha: TextView
    private lateinit var izoh: TextView

    fun korsat() {
        if (qavat != null) return

        val dp = { v: Int ->
            TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v.toFloat(),
                context.resources.displayMetrics).toInt()
        }

        // Oyna o'lchangan bo'sh to'rtburchakdan chiqib ketmasligi kerak.
        val engKeng = (context.resources.displayMetrics.widthPixels * ENI).toInt()
        sarlavha = TextView(context).apply {
            setTextColor(Color.WHITE)
            textSize = 17f
            maxWidth = engKeng
            setTypeface(typeface, android.graphics.Typeface.BOLD)
        }
        izoh = TextView(context).apply {
            setTextColor(Color.parseColor("#C8D4E0"))
            textSize = 12f
            maxWidth = engKeng
        }

        qavat = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(12), dp(8), dp(12), dp(8))
            background = GradientDrawable().apply {
                cornerRadius = dp(10).toFloat()
                setColor(Color.parseColor("#E6101820"))
                setStroke(dp(1), Color.parseColor("#4488AACC"))
            }
            addView(sarlavha)
            addView(izoh)
        }

        val turi = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else
            @Suppress("DEPRECATION") WindowManager.LayoutParams.TYPE_PHONE

        val lp = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            turi,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or
                    WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS or
                    WindowManager.LayoutParams.FLAG_SECURE,
            android.graphics.PixelFormat.TRANSLUCENT,
        ).apply {
            val ekran = context.resources.displayMetrics
            gravity = Gravity.TOP or Gravity.START
            x = (ekran.widthPixels * CHAP).toInt()
            y = (ekran.heightPixels * TEPA).toInt()
        }

        wm.addView(qavat, lp)
        yoz("kuzatilyapti…", "o'yin boshlanishini kutyapman")
    }

    fun yoz(bosh: String, tafsilot: String) {
        qavat?.post {
            sarlavha.text = bosh
            izoh.text = tafsilot
            izoh.visibility = if (tafsilot.isEmpty()) android.view.View.GONE else android.view.View.VISIBLE
        }
    }

    fun yashir() {
        qavat?.let { wm.removeView(it) }
        qavat = null
    }
}
