package ir.javanrood.client

import android.content.Context
import android.os.Build
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.time.Instant

/**
 * ثبت آخرین خطای کنترل‌نشده در فضای خصوصی برنامه.
 * در اجرای بعدی گزارش روی صفحه فعال‌سازی نمایش داده می‌شود.
 */
object NativeCrashStore {
    private const val FILE_NAME = "last_native_crash.txt"

    fun install(context: Context) {
        val applicationContext = context.applicationContext
        val previous = Thread.getDefaultUncaughtExceptionHandler()

        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            runCatching {
                crashFile(applicationContext).writeText(
                    buildString {
                        appendLine("Javanrood Native Android crash report")
                        appendLine("Time: ${Instant.now()}")
                        appendLine("Thread: ${thread.name}")
                        appendLine("Android: ${Build.VERSION.RELEASE} / API ${Build.VERSION.SDK_INT}")
                        appendLine("Device: ${Build.MANUFACTURER} ${Build.MODEL}")
                        appendLine()
                        append(stackTrace(throwable))
                    },
                    Charsets.UTF_8,
                )
            }
            previous?.uncaughtException(thread, throwable)
        }
    }

    fun readLast(context: Context): String? {
        val file = crashFile(context.applicationContext)
        if (!file.exists()) return null
        return runCatching { file.readText(Charsets.UTF_8) }
            .getOrNull()
            ?.takeIf { it.isNotBlank() }
    }

    fun clear(context: Context) {
        runCatching { crashFile(context.applicationContext).delete() }
    }

    private fun crashFile(context: Context): File =
        File(context.filesDir, FILE_NAME)

    private fun stackTrace(throwable: Throwable): String {
        val writer = StringWriter()
        throwable.printStackTrace(PrintWriter(writer))
        return writer.toString()
    }
}
