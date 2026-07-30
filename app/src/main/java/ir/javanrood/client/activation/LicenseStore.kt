package ir.javanrood.client.activation

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import java.time.temporal.ChronoUnit

enum class LicenseState {
NOT_ACTIVATED,
VALID,
NOT_YET_VALID,
EXPIRED,
BLOCKED,
CLOCK_ROLLBACK,
CORRUPTED,
}

data class LicenseStatus(
val state: LicenseState,
val message: String,
val payload: JsonObject? = null,
val remainingDays: Long? = null,
)

class LicenseStore(
private val secureStore: SecureBlobStore,
private val identity: DeviceIdentity,
) {
private val json = Json {
    ignoreUnknownKeys = false
    isLenient = false
    explicitNulls = true
}

private val stateName = "license_state"

fun load(): JsonObject? {
    val clear = secureStore.read(stateName) ?: return null
    return try {
        json.parseToJsonElement(
            clear.toString(Charsets.UTF_8),
        ) as JsonObject
    } catch (error: Exception) {
        throw ActivationException(
            "مجوز محلی آسیب دیده است.",
            error,
        )
    } finally {
        clear.fill(0)
    }
}

fun install(
    activationJson: String,
    nationalCode: String,
): JsonObject {
    val current = load()
    val trustedSignPublic = current?.string(
        "_trusted_admin_sign_public",
    )
    val result = ActivationCodec.openActivationFile(
        jsonText = activationJson,
        nationalCode = nationalCode,
        trustedSignPublic = trustedSignPublic,
    )

    var payloadMap = result.payload.toMutableMap()

    if (result.payload.string("device_id") != identity.deviceId) {
        throw ActivationException(
            "این فایل برای دستگاه دیگری صادر شده است.",
        )
    }

    val localPublic = Base64Url.encode(
        Ed25519PrivateKeyParameters(
            identity.privateSigningSeed,
        )
            .generatePublicKey()
            .encoded,
    )
    val requestedPublic = result.payload.string(
        "client_sign_public",
    )
    if (
        requestedPublic != null &&
        requestedPublic != localPublic
    ) {
        throw ActivationException(
            "کلید امضای این دستگاه با درخواست فعال‌سازی تطابق ندارد.",
        )
    }

    if (current != null) {
        if (
            result.payload.string("license_id") !=
            current.string("license_id")
        ) {
            throw ActivationException(
                "فایل انتخابی مربوط به مجوز دیگری است.",
            )
        }

        listOf(
            "zone_id",
            "committee_code",
            "device_id",
        ).forEach { field ->
            if (
                result.payload.string(field).orEmpty() !=
                current.string(field).orEmpty()
            ) {
                throw ActivationException(
                    "فایل تمدید نمی‌تواند محدوده دسترسی یا دستگاه را تغییر دهد.",
                )
            }
        }

        val merged = current.toMutableMap()
        merged.putAll(payloadMap)
        if (!result.payload.containsKey("password_hash")) {
            current["password_hash"]?.let {
                merged["password_hash"] = it
            }
        }
        payloadMap = merged
    }

    val now = ActivationCodec.utcNowIso()
    payloadMap["installed_at"] = JsonPrimitive(now)
    payloadMap["last_seen_utc"] = JsonPrimitive(now)
    payloadMap["_trusted_admin_sign_public"] = JsonPrimitive(
        result.trustBundle.string("sign_public").orEmpty(),
    )
    payloadMap["_trusted_admin_exchange_public"] = JsonPrimitive(
        result.trustBundle.string("exchange_public").orEmpty(),
    )
    payloadMap["_trusted_admin_sign_fingerprint"] = JsonPrimitive(
        result.trustBundle.string("sign_fingerprint").orEmpty(),
    )

    val payload = JsonObject(payloadMap)
    secureStore.write(
        stateName,
        json.encodeToString<JsonElement>(payload)
            .toByteArray(Charsets.UTF_8),
    )
    return payload
}

fun validate(
    updateClock: Boolean = true,
): LicenseStatus {
    val state = try {
        load()
    } catch (error: ActivationException) {
        return LicenseStatus(
            state = LicenseState.CORRUPTED,
            message = error.message
                ?: "مجوز محلی قابل خواندن نیست.",
        )
    } ?: return LicenseStatus(
        state = LicenseState.NOT_ACTIVATED,
        message = "این دستگاه هنوز فعال نشده است.",
    )

    val now = Instant.now()
    val lastSeen = state.string("last_seen_utc")
        ?.let(::parseInstant)
        ?: now

    if (now.epochSecond + 300 < lastSeen.epochSecond) {
        return LicenseStatus(
            state = LicenseState.CLOCK_ROLLBACK,
            message = "ساعت دستگاه نسبت به آخرین اجرای معتبر به عقب برگشته است.",
            payload = state,
        )
    }

    val rawStatus = state.string("status")
    if (rawStatus != null && rawStatus != "فعال") {
        return LicenseStatus(
            state = LicenseState.BLOCKED,
            message = "مجوز در وضعیت «$rawStatus» قرار دارد.",
            payload = state,
        )
    }

    val validFrom = state.string("valid_from")
        ?.let { parseBoundary(it, endOfDay = false) }
    val validUntil = state.string("valid_until")
        ?.let { parseBoundary(it, endOfDay = true) }

    if (validFrom != null && now.isBefore(validFrom)) {
        return LicenseStatus(
            state = LicenseState.NOT_YET_VALID,
            message = "تاریخ شروع اعتبار این کلاینت هنوز نرسیده است.",
            payload = state,
        )
    }

    if (validUntil != null && now.isAfter(validUntil)) {
        return LicenseStatus(
            state = LicenseState.EXPIRED,
            message = "اعتبار کلاینت در تاریخ ${state.string("valid_until")} پایان یافته است.",
            payload = state,
        )
    }

    val remainingDays = validUntil?.let {
        maxOf(
            0L,
            ChronoUnit.DAYS.between(
                now.atZone(ZoneOffset.UTC).toLocalDate(),
                it.atZone(ZoneOffset.UTC).toLocalDate(),
            ) + 1,
        )
    }

    if (updateClock) {
        val updated = JsonObject(
            state + (
                "last_seen_utc" to
                    JsonPrimitive(ActivationCodec.utcNowIso())
                ),
        )
        secureStore.write(
            stateName,
            json.encodeToString<JsonElement>(updated)
                .toByteArray(Charsets.UTF_8),
        )
    }

    return LicenseStatus(
        state = LicenseState.VALID,
        message = "مجوز معتبر است.",
        payload = state,
        remainingDays = remainingDays,
    )
}

private fun parseInstant(value: String): Instant? =
    runCatching { Instant.parse(value) }.getOrNull()

private fun parseBoundary(
    value: String,
    endOfDay: Boolean,
): Instant? {
    if ('T' in value) {
        return parseInstant(
            value.replace("+00:00", "Z"),
        )
    }

    return runCatching {
        val date = LocalDate.parse(value)
        if (endOfDay) {
            date.plusDays(1)
                .atStartOfDay(ZoneOffset.UTC)
                .toInstant()
                .minusSeconds(1)
        } else {
            date.atStartOfDay(ZoneOffset.UTC).toInstant()
        }
    }.getOrNull()
}
}
