package uz.shamsiyev.oyin.core

/**
 * Mavjud o'yinlar ro'yxati. Android ilovasi old oynadagi paket nomiga qarab
 * mos adapterni shu yerdan oladi.
 */
object GameRegistry {
    private val adapters = LinkedHashMap<String, GameAdapter<*>>()

    fun register(adapter: GameAdapter<*>) {
        adapters[adapter.id] = adapter
    }

    fun byId(id: String): GameAdapter<*>? = adapters[id]

    fun forPackage(packageName: String): GameAdapter<*>? =
        adapters.values.firstOrNull { packageName in it.packageNames }

    fun all(): List<GameAdapter<*>> = adapters.values.toList()
}
