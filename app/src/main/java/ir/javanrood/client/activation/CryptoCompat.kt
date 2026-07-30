package ir.javanrood.client.activation

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import org.bouncycastle.crypto.generators.SCrypt
import org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters
import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters
import org.bouncycastle.math.ec.rfc8032.Ed25519
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.time.Instant
import java.time.temporal.ChronoUnit
import java.util.Base64
import java.util.UUID
import javax.crypto.AEADBadTagException
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

const val REQUEST_FORMAT = "JAVANROOD-CLIENT-REQUEST"
const val ACTIVATION_FORMAT = "JAVANROOD-CLIENT-ACTIVATION"
const val ADMIN_TRUST_FORMAT = "JAVANROOD-ADMIN-TRUST"
const val FORMAT_VERSION = 1

class ActivationException(message: String, cause: Throwable? = null) :
    IllegalArgumentException(message, cause)

class SignatureException(message: String, cause: Throwable? = null) :
    ActivationException(message, cause)

class DecryptionException(message: String, cause: Throwable? = null) :
    ActivationException(message, cause)

data class ActivationOpenResult(
    val payload: JsonObject,
    val trustBundle: JsonObject,
    val envelope: JsonObject,
)

object Base64Url {
    fun encode(value: ByteArray): String =
        Base64.getUrlEncoder().encodeToString(value)

    fun decode(value: String?): ByteArray {
        try {
            return Base64.getUrlDecoder().decode(value.orEmpty())
        } catch (error: IllegalArgumentException) {
            throw ActivationException(
                "ساختار داده رمزنگاری‌شده معتبر نیست.",
                error,
            )
        }
    }
}

object ActivationCodec {
    private val parser = Json {
        ignoreUnknownKeys = false
        isLenient = false
        explicitNulls = true
    }

    private val prettyJson = Json {
        prettyPrint = true
        explicitNulls = true
    }

    fun utcNowIso(): String =
        Instant.now()
            .truncatedTo(ChronoUnit.SECONDS)
            .toString()

    fun normalizeNationalCode(value: String): String {
        val normalized = buildString {
            value.forEach { character ->
                when (character) {
                    in '0'..'9' -> append(character)
                    in '۰'..'۹' -> append('0' + (character - '۰'))
                    in '٠'..'٩' -> append('0' + (character - '٠'))
                }
            }
        }

        if (normalized.length != 10) {
            throw ActivationException("کد ملی باید دقیقاً ۱۰ رقم باشد.")
        }
        return normalized
    }

    fun sha256Hex(value: ByteArray): String =
        MessageDigest.getInstance("SHA-256")
            .digest(value)
            .joinToString(separator = "") { byte ->
                "%02x".format(byte.toInt() and 0xFF)
            }

    fun nationalCodeHash(value: String): String =
        sha256Hex(
            normalizeNationalCode(value)
                .toByteArray(StandardCharsets.US_ASCII),
        )

    fun publicFingerprint(rawKey: ByteArray): String {
        val digest = sha256Hex(rawKey).uppercase()
        return (0 until 32 step 4)
            .joinToString(":") { index ->
                digest.substring(index, index + 4)
            }
    }

    fun buildActivationRequest(
        nationalCode: String,
        deviceId: String,
        privateSeed: ByteArray,
        clientVersion: String,
        requestId: String = UUID.randomUUID().toString(),
        createdAt: String = utcNowIso(),
    ): JsonObject {
        require(privateSeed.size == Ed25519PrivateKeyParameters.KEY_SIZE) {
            "اندازه کلید خصوصی Ed25519 معتبر نیست."
        }
        if (!deviceId.matches(Regex("[0-9a-f]{64}"))) {
            throw ActivationException("شناسه دستگاه معتبر نیست.")
        }

        val privateKey = Ed25519PrivateKeyParameters(privateSeed)
        val publicKey = privateKey.generatePublicKey().encoded

        val core = buildJsonObject {
            put("format", REQUEST_FORMAT)
            put("version", FORMAT_VERSION)
            put("request_id", requestId)
            put("created_at", createdAt)
            put("device_id", deviceId)
            put("national_code_hash", nationalCodeHash(nationalCode))
            put("client_sign_public", Base64Url.encode(publicKey))
            put("client_version", clientVersion)
        }

        val message = CanonicalJson.encode(core)
            .toByteArray(StandardCharsets.UTF_8)
        val signature = ByteArray(
            Ed25519PrivateKeyParameters.SIGNATURE_SIZE,
        )
        privateKey.sign(
            Ed25519.Algorithm.Ed25519,
            null,
            message,
            0,
            message.size,
            signature,
            0,
        )

        return JsonObject(
            core + ("signature" to JsonPrimitive(
                Base64Url.encode(signature),
            )),
        )
    }

    fun requestToPrettyJson(request: JsonObject): String =
        prettyJson.encodeToString<JsonElement>(request)

    fun openActivationFile(
        jsonText: String,
        nationalCode: String,
        trustedSignPublic: String? = null,
    ): ActivationOpenResult {
        val code = normalizeNationalCode(nationalCode)
        val envelope = try {
            parser.parseToJsonElement(jsonText).jsonObject
        } catch (error: Exception) {
            throw ActivationException(
                "فایل فعال‌سازی قابل خواندن نیست.",
                error,
            )
        }

        if (
            envelope.string("format") != ACTIVATION_FORMAT ||
            envelope.int("version") != FORMAT_VERSION
        ) {
            throw ActivationException(
                "فرمت فایل فعال‌سازی پشتیبانی نمی‌شود.",
            )
        }

        val signRaw = Base64Url.decode(
            envelope.string("admin_sign_public"),
        )
        if (
            trustedSignPublic != null &&
            !MessageDigest.isEqual(
                Base64Url.decode(trustedSignPublic),
                signRaw,
            )
        ) {
            throw SignatureException(
                "این فایل توسط مدیر مورد اعتماد این کلاینت صادر نشده است.",
            )
        }

        verifyEnvelopeSignature(envelope, signRaw)

        val licenseId = envelope.string("license_id")
            ?: throw ActivationException("شناسه مجوز در فایل وجود ندارد.")
        val salt = Base64Url.decode(envelope.string("salt"))
        val nonce = Base64Url.decode(envelope.string("nonce"))
        val ciphertext = Base64Url.decode(envelope.string("ciphertext"))

        val key = SCrypt.generate(
            code.toByteArray(StandardCharsets.US_ASCII),
            salt,
            1 shl 15,
            8,
            1,
            32,
        )

        val payload = try {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(
                Cipher.DECRYPT_MODE,
                SecretKeySpec(key, "AES"),
                GCMParameterSpec(128, nonce),
            )
            cipher.updateAAD(
                activationAad(envelope)
                    .toByteArray(StandardCharsets.UTF_8),
            )
            val clear = cipher.doFinal(ciphertext)
            parser.parseToJsonElement(
                clear.toString(StandardCharsets.UTF_8),
            ).jsonObject
        } catch (error: AEADBadTagException) {
            throw DecryptionException(
                "کد ملی با فایل فعال‌سازی تطابق ندارد یا فایل دست‌کاری شده است.",
                error,
            )
        } catch (error: Exception) {
            throw DecryptionException(
                "فایل فعال‌سازی رمزگشایی نشد.",
                error,
            )
        } finally {
            key.fill(0)
        }

        val expectedVerifier = sha256Hex(
            "$code|$licenseId".toByteArray(StandardCharsets.US_ASCII),
        )
        if (payload.string("national_code_verifier") != expectedVerifier) {
            throw DecryptionException(
                "کد ملی واردشده با مجوز مطابقت ندارد.",
            )
        }

        if (payload.string("license_id") != licenseId) {
            throw ActivationException(
                "شناسه مجوز در فایل ناسازگار است.",
            )
        }

        val trustBundle = buildJsonObject {
            put("format", ADMIN_TRUST_FORMAT)
            put("version", FORMAT_VERSION)
            put(
                "sign_public",
                envelope.string("admin_sign_public").orEmpty(),
            )
            put(
                "exchange_public",
                envelope.string("admin_exchange_public").orEmpty(),
            )
            put(
                "sign_fingerprint",
                envelope.string("admin_sign_fingerprint")
                    ?: publicFingerprint(signRaw),
            )
        }

        return ActivationOpenResult(
            payload = payload,
            trustBundle = trustBundle,
            envelope = envelope,
        )
    }

    private fun verifyEnvelopeSignature(
        envelope: JsonObject,
        signRaw: ByteArray,
    ) {
        val signature = Base64Url.decode(
            envelope.string("signature"),
        )
        val core = JsonObject(
            envelope.filterKeys { key -> key != "signature" },
        )
        val message = CanonicalJson.encode(core)
            .toByteArray(StandardCharsets.UTF_8)

        val valid = try {
            Ed25519PublicKeyParameters(signRaw).verify(
                Ed25519.Algorithm.Ed25519,
                null,
                message,
                0,
                message.size,
                signature,
                0,
            )
        } catch (_: Exception) {
            false
        }

        if (!valid) {
            throw SignatureException(
                "امضای فایل فعال‌سازی معتبر نیست.",
            )
        }
    }

    private fun activationAad(envelope: JsonObject): String {
        val aad = buildJsonObject {
            put("format", envelope.string("format").orEmpty())
            put("version", envelope.int("version"))
            put("kind", envelope.string("kind").orEmpty())
            put("license_id", envelope.string("license_id").orEmpty())
            put("issued_at", envelope.string("issued_at").orEmpty())
        }
        return CanonicalJson.encode(aad)
    }
}

internal fun JsonObject.string(name: String): String? =
    get(name)?.jsonPrimitive?.contentOrNull

internal fun JsonObject.int(name: String): Int =
    get(name)?.jsonPrimitive?.intOrNull ?: 0
