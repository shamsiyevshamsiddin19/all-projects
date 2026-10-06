plugins {
    kotlin("jvm")
    application
}

kotlin { jvmToolchain(17) }

dependencies {
    api(project(":cards"))
    testImplementation(kotlin("test"))
}

application { mainClass.set("uz.shamsiyev.oyin.durak.SelfPlayKt") }

/** ./gradlew :games:durak:benchmark --args="300 2 60" */
tasks.register<JavaExec>("benchmark") {
    group = "verification"
    description = "Monte-Carlo bot qoidali botga qarshi"
    mainClass.set("uz.shamsiyev.oyin.durak.BenchmarkKt")
    classpath = sourceSets["main"].runtimeClasspath
}

tasks.test { useJUnitPlatform() }

/** ./gradlew :games:durak:demo */
tasks.register<JavaExec>("demo") {
    group = "application"
    description = "Maslahat qanday ko'rinishini ko'rsatadi"
    mainClass.set("uz.shamsiyev.oyin.durak.DemoKt")
    classpath = sourceSets["main"].runtimeClasspath
}

/** Ekrandan o'qilgan holatdan maslahat: ./gradlew :games:durak:maslahat --args="..." */
tasks.register<JavaExec>("maslahat") {
    group = "application"
    description = "Ekrandan o'qilgan holatdan maslahat beradi"
    mainClass.set("uz.shamsiyev.oyin.durak.MaslahatKt")
    classpath = sourceSets["main"].runtimeClasspath
}
