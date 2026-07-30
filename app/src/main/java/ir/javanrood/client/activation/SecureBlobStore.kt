package ir.javanrood.client.activation

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.io.File
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureBlobStore(
context: Context,
) {
private val root: File = File(
    context.filesDir,
    "activation_security",
).apply {
    mkdirs()
}

private val keyAlias = "javanrood_activation_v1"

fun write(name: String, clear: ByteArray) {
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
    cipher.updateAAD(name.toByteArray(Charsets.UTF_8))

    val encrypted = cipher.doFinal(clear)
    val iv = cipher.iv
    require(iv.size <= 255) {
        "اندازه IV معتبر نیست."
    }

    val output = ByteArray(2 + iv.size + encrypted.size)
    output[0] = 1
    output[1] = iv.size.toByte()
    iv.copyInto(output, destinationOffset = 2)
    encrypted.copyInto(
        output,
        destinationOffset = 2 + iv.size,
    )

    val target = fileFor(name)
    val temporary = File(target.parentFile, "${target.name}.tmp")
    temporary.outputStream().use { stream ->
        stream.write(output)
        stream.fd.sync()
    }

    if (target.exists() && !target.delete()) {
        temporary.delete()
        error("فایل امن قبلی حذف نشد.")
    }
    if (!temporary.renameTo(target)) {
        temporary.delete()
        error("ذخیره امن اطلاعات انجام نشد.")
    }
}

fun read(name: String): ByteArray? {
    val file = fileFor(name)
    if (!file.exists()) return null

    val blob = file.readBytes()
    if (blob.size < 3 || blob[0].toInt() != 1) {
        throw ActivationException(
            "ساختار اطلاعات امن برنامه معتبر نیست.",
        )
    }

    val ivSize = blob[1].toInt() and 0xFF
    if (ivSize <= 0 || blob.size <= 2 + ivSize) {
        throw ActivationException(
            "اطلاعات امن برنامه ناقص است.",
        )
    }

    val iv = blob.copyOfRange(2, 2 + ivSize)
    val encrypted = blob.copyOfRange(
        2 + ivSize,
        blob.size,
    )

    return try {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(
            Cipher.DECRYPT_MODE,
            getOrCreateKey(),
            GCMParameterSpec(128, iv),
        )
        cipher.updateAAD(name.toByteArray(Charsets.UTF_8))
        cipher.doFinal(encrypted)
    } catch (error: Exception) {
        throw ActivationException(
            "اطلاعات امن برنامه قابل بازیابی نیست.",
            error,
        )
    }
}

fun getOrCreateRandom(
    name: String,
    size: Int,
): ByteArray {
    read(name)?.let { existing ->
        if (existing.size != size) {
            throw ActivationException(
                "اندازه داده امن ذخیره‌شده معتبر نیست.",
            )
        }
        return existing
    }

    val generated = ByteArray(size).also {
        java.security.SecureRandom().nextBytes(it)
    }
    write(name, generated)
    return generated
}

private fun fileFor(name: String): File {
    require(name.matches(Regex("[a-z0-9_\\-]+"))) {
        "نام داده امن معتبر نیست."
    }
    return File(root, "$name.bin")
}

private fun getOrCreateKey(): SecretKey {
    val keyStore = KeyStore
        .getInstance("AndroidKeyStore")
        .apply { load(null) }

    (keyStore.getKey(keyAlias, null) as? SecretKey)?.let {
        return it
    }

    return KeyGenerator
        .getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            "AndroidKeyStore",
        )
        .apply {
            init(
                KeyGenParameterSpec.Builder(
                    keyAlias,
                    KeyProperties.PURPOSE_ENCRYPT or
                        KeyProperties.PURPOSE_DECRYPT,
                )
                    .setBlockModes(
                        KeyProperties.BLOCK_MODE_GCM,
                    )
                    .setEncryptionPaddings(
                        KeyProperties.ENCRYPTION_PADDING_NONE,
                    )
                    .setKeySize(256)
                    .setRandomizedEncryptionRequired(true)
                    .build(),
            )
        }
        .generateKey()
}
}
