plugins { kotlin("jvm") }
kotlin { jvmToolchain(17) }
dependencies {
    api(project(":core"))
    testImplementation(kotlin("test"))
}
tasks.test { useJUnitPlatform() }
