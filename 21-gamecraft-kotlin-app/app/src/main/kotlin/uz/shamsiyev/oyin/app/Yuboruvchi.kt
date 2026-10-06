package uz.shamsiyev.oyin.app

import android.util.Log
import java.net.HttpURLConnection
import java.net.URL

/**
 * Tashxis kadrlarini serverga yuboradi.
 *
 * Telefonda jurnalga kirish imkoni yo'q, shuning uchun ilova ko'rgan kadrni
 * o'zi yuboradi. Server - foydalanuvchining o'z serveri, manzil tasodifiy
 * yo'l ortida turadi.
 *
 * Yuborib bo'lmasa jim qoladi va kadr telefonning o'ziga saqlanadi:
 * tashxis ishlamagani uchun ilovaning asosiy vazifasi to'xtab qolmasligi kerak.
 */
class Yuboruvchi(private val manzil: String) {

    fun yubor(nom: String, malumot: ByteArray, turi: String): Boolean = try {
        val ulanish = (URL(manzil).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 8000
            readTimeout = 12000
            doOutput = true
            setRequestProperty("X-Nom", nom)
            setRequestProperty("Content-Type", turi)
            setFixedLengthStreamingMode(malumot.size)
        }
        try {
            ulanish.outputStream.use { it.write(malumot) }
            ulanish.responseCode in 200..299
        } finally {
            ulanish.disconnect()
        }
    } catch (e: Throwable) {
        Log.w("OyinYordamchi", "tashxis yuborilmadi: ${e.message}")
        false
    }
}
