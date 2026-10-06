import java.util.Properties

plugins {
    id("com.android.application")
    kotlin("android")
}

/**
 * Tashxis serverining manzili KODDA TURMAYDI: u tasodifiy yo'l ortidagi
 * ochiq yuklash nuqtasi, ya'ni maxfiy. Manzil `local.properties` ichida
 * (u git'ga tushmaydi) yoki `-Ptashxis.manzili=...` bilan beriladi.
 * Berilmasa tashxis serverga yubormaydi - kadr telefonning o'ziga saqlanadi.
 */
val tashxisManzili: String = run {
    val fayl = rootProject.file("local.properties")
    val xos = if (fayl.exists()) Properties().apply { fayl.inputStream().use { load(it) } } else null
    (project.findProperty("tashxis.manzili") as String?)
        ?: xos?.getProperty("tashxis.manzili")
        ?: ""
}

android {
    namespace = "uz.shamsiyev.oyin.app"
    compileSdk = 35
    // Mashinada o'rnatilgani ishlatiladi: yuklab olish imkoni yo'q.
    buildToolsVersion = "36.0.0"

    defaultConfig {
        applicationId = "uz.shamsiyev.oyin.app"
        minSdk = 26          // TYPE_APPLICATION_OVERLAY shu versiyadan
        targetSdk = 34
        versionCode = 1
        versionName = "0.1"
    }

    buildFeatures { buildConfig = true }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    defaultConfig.buildConfigField("String", "TASHXIS_MANZILI", "\"$tashxisManzili\"")

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions { jvmTarget = "17" }

    sourceSets["main"].kotlin.srcDir("src/main/kotlin")
    // Shablon banki loyihada bitta joyda turadi, nusxa ko'chirilmaydi.
    sourceSets["main"].assets.srcDir("$rootDir/games/durak/profil")
}

dependencies {
    // Boshqa kutubxona yo'q: faqat Android SDK va loyihaning o'z qatlamlari.
    implementation(project(":games:durak"))
}
