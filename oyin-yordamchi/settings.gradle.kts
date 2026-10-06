pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "oyin-yordamchi"

// Qatlamlar: core (o'yindan mustaqil) <- cards (karta o'yinlari uchun umumiy) <- games/*
// app  - Android ilovasi, faqat core bilan gaplashadi
// desktop - kompyuterda sinash uchun
include("core")
include("cards")
include("games:durak")
include("desktop")
include("app")
