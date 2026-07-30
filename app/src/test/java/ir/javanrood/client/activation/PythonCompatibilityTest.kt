package ir.javanrood.client.activation

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PythonCompatibilityTest {
private fun resource(name: String): String =
    requireNotNull(
        javaClass.classLoader?.getResource(name),
    ).readText(Charsets.UTF_8)

@Test
fun kotlinRequestMatchesPythonReferenceSignature() {
    val seed = ByteArray(32) { index -> index.toByte() }
    val request = ActivationCodec.buildActivationRequest(
        nationalCode = "1234567890",
        deviceId = "a".repeat(64),
        privateSeed = seed,
        clientVersion = "1.0.0-native-phase1",
        requestId = "11111111-2222-3333-4444-555555555555",
        createdAt = "2026-07-30T05:00:00Z",
    )

    val expected = Json.parseToJsonElement(
        resource("python_request_fixture.jrr"),
    ).jsonObject

    expected.entries.forEach { entry ->
        assertEquals(
            "field=${entry.key}",
            entry.value,
            request[entry.key],
        )
    }
}

@Test
fun kotlinOpensPythonActivationFile() {
    val result = ActivationCodec.openActivationFile(
        jsonText = resource("python_activation_fixture.jra"),
        nationalCode = "1234567890",
    )

    assertEquals(
        "کاربر آزمایشی",
        result.payload["responsible_full_name"]
            ?.jsonPrimitive
            ?.contentOrNull,
    )
    assertEquals(
        "بلوک ۱",
        result.payload["zone_name"]
            ?.jsonPrimitive
            ?.contentOrNull,
    )
    assertEquals(
        "کمیته اجتماعی",
        result.payload["committee_title"]
            ?.jsonPrimitive
            ?.contentOrNull,
    )
    assertEquals(
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        result.payload["license_id"]
            ?.jsonPrimitive
            ?.contentOrNull,
    )
    assertTrue(
        result.trustBundle["sign_public"]
            ?.jsonPrimitive
            ?.contentOrNull
            .orEmpty()
            .isNotBlank(),
    )
}

@Test(expected = DecryptionException::class)
fun wrongNationalCodeCannotOpenActivation() {
    ActivationCodec.openActivationFile(
        jsonText = resource("python_activation_fixture.jra"),
        nationalCode = "0000000000",
    )
}
}
