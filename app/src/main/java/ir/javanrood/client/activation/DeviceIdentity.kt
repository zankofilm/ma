package ir.javanrood.client.activation

import android.content.Context
import android.provider.Settings
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets

class DeviceIdentity(
private val context: Context,
private val secureStore: SecureBlobStore,
) {
val privateSigningSeed: ByteArray
    get() = secureStore.getOrCreateRandom(
        name = "client_ed25519_seed",
        size = 32,
    )

val deviceId: String
    get() {
        val installationSeed = secureStore.getOrCreateRandom(
            name = "device_identity_seed",
            size = 32,
        )
        val androidId = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ANDROID_ID,
        ).orEmpty()

        val packageName = context.packageName
        val androidBytes = androidId.toByteArray(
            StandardCharsets.UTF_8,
        )
        val packageBytes = packageName.toByteArray(
            StandardCharsets.UTF_8,
        )

        val material = ByteBuffer.allocate(
            installationSeed.size +
                androidBytes.size +
                packageBytes.size +
                2,
        )
            .put(installationSeed)
            .put(0)
            .put(androidBytes)
            .put(0)
            .put(packageBytes)
            .array()

        return ActivationCodec.sha256Hex(material)
    }
}
