package ir.javanrood.client.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val JavanroodColorScheme = darkColorScheme(
primary = Color(0xFFD4A63A),
onPrimary = Color(0xFF071B33),
secondary = Color(0xFF4EA5D9),
onSecondary = Color.White,
background = Color(0xFF061326),
onBackground = Color(0xFFF4F7FB),
surface = Color(0xFF0D2440),
onSurface = Color(0xFFF4F7FB),
surfaceVariant = Color(0xFF173451),
onSurfaceVariant = Color(0xFFD6E4F0),
error = Color(0xFFFFB4AB),
onError = Color(0xFF690005),
)

@Composable
fun JavanroodTheme(
content: @Composable () -> Unit,
) {
MaterialTheme(
    colorScheme = JavanroodColorScheme,
    content = content,
)
}
