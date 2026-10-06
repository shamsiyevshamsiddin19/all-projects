plugins {
    id("com.android.application")
    kotlin("android")
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

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

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
