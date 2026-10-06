package uz.shamsiyev.oyin.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.util.DisplayMetrics
import android.util.Log
import android.view.WindowManager
import uz.shamsiyev.oyin.core.Frame
import uz.shamsiyev.oyin.durak.DurakAdvisor
import uz.shamsiyev.oyin.durak.DurakKoz
import uz.shamsiyev.oyin.durak.DurakProfil
import uz.shamsiyev.oyin.durak.Kuzatuv

/**
 * Ekranni o'qib, maslahatni overlay'ga chiqaradigan xizmat.
 *
 * Ekran sekundiga ikki marta o'qiladi va faqat TINCHLANGANDA tahlil qilinadi:
 * karta uchib kelayotgan paytda o'qilsa holat chalkashadi. Shuningdek ekran
 * o'zgarmagan bo'lsa umuman ishlamaydi - batareya uchun.
 */
class EkranXizmati : Service() {

    companion object {
        const val KANAL = "oyin_yordamchi"
        const val BILDIRISHNOMA = 1
        const val NATIJA_KODI = "natija_kodi"
        const val NATIJA_MALUMOT = "natija_malumot"
        private const val TAG = "OyinYordamchi"

        /** Tanish shu kenglikda o'rgatilgan; ekran shunga keltiriladi. */
        const val ISHCHI_KENGLIK = 864

        /** Ekran shu darajadan kam o'zgarsa - tinchlangan hisoblanadi. */
        private const val TINCHLIK_CHEGARASI = 0.004

        /** Shundan kam farq bo'lsa - yangi narsa yo'q, tahlil qilinmaydi. */
        private const val YANGILIK_CHEGARASI = 0.002

        /** Ekran soniyasiga 60 marta yangilanadi; bizga sekundiga ikki marta yetadi. */
        private const val ORALIQ_MS = 450L
    }

    private var projection: MediaProjection? = null
    private var virtual: VirtualDisplay? = null
    private var reader: ImageReader? = null
    private var ish: HandlerThread? = null
    private lateinit var overlay: Overlay

    private var koz: DurakKoz? = null
    private var kuzatuv = Kuzatuv(raqiblarSoni = 2)
    private val maslahatchi = DurakAdvisor()

    private var oldingiKadr: Frame? = null
    private var tahlilQilingan: Frame? = null
    private var oxirgiOqish = 0L
    private var pikselBuferi: IntArray? = null
    private var qatorBuferi: ByteArray? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        overlay = Overlay(this)
        koz = DurakProfil.oqi { nom -> assets.open(nom) }.let { DurakKoz(it) }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Android 29+ da ekranni o'qishdan OLDIN xizmat old planda bo'lishi shart.
        oldPlangaChiq()
        overlay.korsat()

        val kod = intent?.getIntExtra(NATIJA_KODI, 0) ?: 0
        val malumot = if (Build.VERSION.SDK_INT >= 33)
            intent?.getParcelableExtra(NATIJA_MALUMOT, Intent::class.java)
        else
            @Suppress("DEPRECATION") intent?.getParcelableExtra(NATIJA_MALUMOT)

        if (kod == 0 || malumot == null) {
            overlay.yoz("ruxsat yo'q", "ekranni o'qishga ruxsat berilmadi")
            return START_NOT_STICKY
        }

        val mgr = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        projection = mgr.getMediaProjection(kod, malumot).apply {
            registerCallback(object : MediaProjection.Callback() {
                override fun onStop() {
                    Log.i(TAG, "ekranni o'qish to'xtadi")
                    stopSelf()
                }
            }, Handler(mainLooper))
        }
        ekranniOqishniBoshla()
        return START_STICKY
    }

    private fun oldPlangaChiq() {
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            nm.createNotificationChannel(
                NotificationChannel(KANAL, "O'yin yordamchisi", NotificationManager.IMPORTANCE_LOW)
            )
        }
        val bildirishnoma: Notification = Notification.Builder(this, KANAL)
            .setContentTitle("O'yin yordamchisi ishlayapti")
            .setContentText("ekran o'qilyapti")
            .setSmallIcon(android.R.drawable.ic_menu_view)
            .build()
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(BILDIRISHNOMA, bildirishnoma,
                android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(BILDIRISHNOMA, bildirishnoma)
        }
    }

    private fun ekranniOqishniBoshla() {
        val wm = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val metrics = DisplayMetrics()
        @Suppress("DEPRECATION") wm.defaultDisplay.getRealMetrics(metrics)

        // Tanish 864 piksel kenglikda o'rgatilgan: o'lchamlar shunga mos keladi.
        // Ekranni o'sha kenglikka keltirib beramiz - tizim o'zi kichiklashtiradi.
        val kenglik = ISHCHI_KENGLIK
        val balandlik = (metrics.heightPixels.toLong() * kenglik / metrics.widthPixels).toInt()

        reader = ImageReader.newInstance(kenglik, balandlik, PixelFormat.RGBA_8888, 2)
        ish = HandlerThread("ekran").also { it.start() }
        val handler = Handler(ish!!.looper)

        virtual = projection?.createVirtualDisplay(
            "oyin-yordamchi", kenglik, balandlik, metrics.densityDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            reader!!.surface, null, handler,
        )

        reader?.setOnImageAvailableListener({ r ->
            // Ekran displey tezligida yangilanadi. Har kadrni to'liq o'qish -
            // sekundiga o'nlab marta 6 MB massiv ajratish degani; telefon qiziydi.
            // Shuning uchun oraliqdan tezrog'i shunchaki tashlab yuboriladi.
            val hozir = android.os.SystemClock.uptimeMillis()
            if (hozir - oxirgiOqish < ORALIQ_MS) {
                r.acquireLatestImage()?.close()
                return@setOnImageAvailableListener
            }
            oxirgiOqish = hozir
            val kadr = kadrniOl(r) ?: return@setOnImageAvailableListener
            try {
                qayta(kadr)
            } catch (e: Throwable) {
                Log.e(TAG, "tahlilda xato", e)
            }
        }, handler)
    }

    /** ImageReader'dan kadr oladi; qator to'ldirishni hisobga oladi. */
    private fun kadrniOl(r: ImageReader): Frame? {
        val img = r.acquireLatestImage() ?: return null
        try {
            val plane = img.planes[0]
            val w = img.width
            val h = img.height
            val qadam = plane.rowStride
            val piksel = plane.pixelStride
            val buf = plane.buffer
            // Har qatorning oxirida to'ldirish bo'lishi mumkin (rowStride > w*pixelStride),
            // shuning uchun qator-qator o'qiladi. Oxirgi qatorda to'ldirish yozilmagan
            // bo'lishi mumkin - faqat kerakli qismi olinadi.
            val kerak = w * piksel
            // Buferlar qayta ishlatiladi: har kadrda yangi massiv ajratish
            // axlat yig'uvchini bekorga yuklaydi.
            val qator = qatorBuferi?.takeIf { it.size == kerak } ?: ByteArray(kerak).also { qatorBuferi = it }
            val px = pikselBuferi?.takeIf { it.size == w * h } ?: IntArray(w * h).also { pikselBuferi = it }
            for (y in 0 until h) {
                buf.position(y * qadam)
                buf.get(qator, 0, minOf(kerak, buf.remaining()))
                for (x in 0 until w) {
                    val o = x * piksel
                    px[y * w + x] = ((qator[o].toInt() and 0xFF) shl 16) or
                            ((qator[o + 1].toInt() and 0xFF) shl 8) or
                            (qator[o + 2].toInt() and 0xFF)
                }
            }
            // Taqqoslash uchun oldingi kadr saqlanadi, shuning uchun nusxa olinadi.
            return Frame(w, h, px.copyOf())
        } finally {
            img.close()
        }
    }

    private fun qayta(kadr: Frame) {
        val oldingi = oldingiKadr
        oldingiKadr = kadr

        // Animatsiya paytida o'qish holatni chalkashtiradi: ekran tinchlanishini kutamiz.
        if (oldingi == null || kadr.diff(oldingi) > TINCHLIK_CHEGARASI) return
        // Ekranda yangilik bo'lmasa, bekorga ishlamaymiz.
        val oxirgi = tahlilQilingan
        if (oxirgi != null && kadr.diff(oxirgi) < YANGILIK_CHEGARASI) return
        tahlilQilingan = kadr

        val k = koz ?: return
        val holat = k.holat(kadr)
        kuzatuv.qadam(holat, System.currentTimeMillis() / 1000.0)

        val view = kuzatuv.dvigatelUchun()
        if (view == null) {
            overlay.yoz("kozir kutilyapti", "o'yin boshidan kuzatilsa aniqroq bo'ladi")
            return
        }
        if (holat.qol.isEmpty()) {
            overlay.yoz("qo'l ko'rinmayapti", "")
            return
        }
        val maslahat = maslahatchi.advise(view)
        val tafsilot = buildString {
            append(maslahat.reason)
            maslahat.caveat?.let { append(" · ").append(it) }
        }
        overlay.yoz(maslahat.headline, tafsilot)
    }

    override fun onDestroy() {
        reader?.setOnImageAvailableListener(null, null)
        virtual?.release()
        reader?.close()
        projection?.stop()
        ish?.quitSafely()
        overlay.yashir()
        super.onDestroy()
    }
}
