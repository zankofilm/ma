package ir.javanrood.client.activation

import android.content.Context
import android.net.Uri
import ir.javanrood.client.BuildConfig
import kotlinx.serialization.json.JsonObject
import java.util.UUID

data class RequestDocument(
val filename: String,
val content: String,
)

class ActivationRepository(
private val context: Context,
) {
private val secureStore = SecureBlobStore(context)
private val identity = DeviceIdentity(
    context = context,
    secureStore = secureStore,
)
private val licenseStore = LicenseStore(
    secureStore = secureStore,
    identity = identity,
)

val deviceId: String
    get() = identity.deviceId

fun status(): LicenseStatus =
    licenseStore.validate(updateClock = false)

fun buildRequest(
    nationalCode: String,
): RequestDocument {
    val request = ActivationCodec.buildActivationRequest(
        nationalCode = nationalCode,
        deviceId = identity.deviceId,
        privateSeed = identity.privateSigningSeed,
        clientVersion = BuildConfig.CLIENT_PROTOCOL_VERSION,
    )

    val filename = buildString {
        append("javanrood_activation_request_")
        append(UUID.randomUUID().toString().take(8))
        append(".jrr")
    }

    return RequestDocument(
        filename = filename,
        content = ActivationCodec.requestToPrettyJson(request),
    )
}

fun writeRequest(
    uri: Uri,
    document: RequestDocument,
) {
    context.contentResolver
        .openOutputStream(uri, "w")
        ?.bufferedWriter(Charsets.UTF_8)
        ?.use { writer ->
            writer.write(document.content)
            writer.flush()
        }
        ?: throw ActivationException(
            "فایل درخواست در مسیر انتخابی ذخیره نشد.",
        )
}

fun installActivation(
    uri: Uri,
    nationalCode: String,
): JsonObject {
    val content = context.contentResolver
        .openInputStream(uri)
        ?.bufferedReader(Charsets.UTF_8)
        ?.use { it.readText() }
        ?: throw ActivationException(
            "فایل فعال‌سازی قابل خواندن نیست.",
        )

    return licenseStore.install(
        activationJson = content,
        nationalCode = nationalCode,
    )
}
}
