package ir.javanrood.client.activation

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import java.math.BigDecimal

/**
 * معادل دقیق json.dumps(..., ensure_ascii=False, sort_keys=True,
 * separators=(",", ":")) در نسخه ادمین Python.
 */
object CanonicalJson {
fun encode(element: JsonElement): String = buildString {
    appendElement(element)
}

private fun StringBuilder.appendElement(element: JsonElement) {
    when (element) {
        JsonNull -> append("null")
        is JsonObject -> appendObject(element)
        is JsonArray -> appendArray(element)
        is JsonPrimitive -> appendPrimitive(element)
    }
}

private fun StringBuilder.appendObject(value: JsonObject) {
    append('{')
    value.entries
        .sortedBy { it.key }
        .forEachIndexed { index, entry ->
            if (index > 0) append(',')
            appendQuoted(entry.key)
            append(':')
            appendElement(entry.value)
        }
    append('}')
}

private fun StringBuilder.appendArray(value: JsonArray) {
    append('[')
    value.forEachIndexed { index, element ->
        if (index > 0) append(',')
        appendElement(element)
    }
    append(']')
}

private fun StringBuilder.appendPrimitive(value: JsonPrimitive) {
    if (value.isString) {
        appendQuoted(value.content)
        return
    }

    val raw = value.content
    when (raw) {
        "true", "false" -> append(raw)
        else -> append(normalizeNumber(raw))
    }
}

private fun normalizeNumber(raw: String): String {
    return try {
        val number = BigDecimal(raw)
        val normalized = number.stripTrailingZeros().toPlainString()
        if (normalized == "-0") "0" else normalized
    } catch (_: NumberFormatException) {
        raw
    }
}

private fun StringBuilder.appendQuoted(value: String) {
    append('"')
    value.forEach { character ->
        when (character) {
            '"' -> append("\\\"")
            '\\' -> append("\\\\")
            '\b' -> append("\\b")
            '\u000C' -> append("\\f")
            '\n' -> append("\\n")
            '\r' -> append("\\r")
            '\t' -> append("\\t")
            else -> {
                if (character.code < 0x20) {
                    append("\\u")
                    append(character.code.toString(16).padStart(4, '0'))
                } else {
                    append(character)
                }
            }
        }
    }
    append('"')
}
}
