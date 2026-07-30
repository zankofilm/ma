package ir.javanrood.client.activation

import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Test

class CanonicalJsonTest {
@Test
fun canonicalJsonMatchesPythonOrderingAndSeparators() {
    val input = Json.parseToJsonElement(
        """
        {
          "z": "فارسی",
          "a": 1,
          "nested": {"b": true, "a": null},
          "items": [3, "x"]
        }
        """.trimIndent(),
    )

    assertEquals(
        """{"a":1,"items":[3,"x"],"nested":{"a":null,"b":true},"z":"فارسی"}""",
        CanonicalJson.encode(input),
    )
}
}
