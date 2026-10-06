plugins {
    kotlin("jvm")
    application
}

kotlin { jvmToolchain(17) }

dependencies { implementation(project(":games:durak")) }

application { mainClass.set("uz.shamsiyev.oyin.desktop.KozCliKt") }

/** Kadrlarni Kotlin ko'zi bilan o'qish: ./gradlew :desktop:koz --args="<papka yoki fayl>" */
tasks.register<JavaExec>("koz") {
    group = "application"
    description = "Kotlin ko'zini PNG kadrlarda ishlatadi"
    mainClass.set("uz.shamsiyev.oyin.desktop.KozCliKt")
    classpath = sourceSets["main"].runtimeClasspath
    // Yo'llar loyiha ildizidan hisoblanadi (profil va kadrlar o'sha yerda).
    workingDir = rootProject.projectDir
}
