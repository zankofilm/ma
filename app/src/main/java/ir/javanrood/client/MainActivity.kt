package ir.javanrood.client

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import ir.javanrood.client.activation.ActivationEvent
import ir.javanrood.client.activation.ActivationUiState
import ir.javanrood.client.activation.ActivationViewModel
import ir.javanrood.client.activation.LicenseState
import ir.javanrood.client.ui.theme.JavanroodTheme
import kotlinx.coroutines.flow.collectLatest
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        NativeCrashStore.install(this)
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val previousCrash = NativeCrashStore.readLast(this)

        setContent {
            JavanroodTheme {
                CompositionLocalProvider(
                    LocalLayoutDirection provides LayoutDirection.Rtl,
                ) {
                    ActivationRoute(
                        previousCrash = previousCrash,
                        onClearPreviousCrash = {
                            NativeCrashStore.clear(this)
                        },
                    )
                }
            }
        }
    }
}

@Composable
private fun ActivationRoute(
    previousCrash: String?,
    onClearPreviousCrash: () -> Unit,
    viewModel: ActivationViewModel = viewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    var visibleCrash by remember { mutableStateOf(previousCrash) }

    val createRequestLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument(
            "application/octet-stream",
        ),
        onResult = viewModel::savePreparedRequest,
    )

    val openActivationLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument(),
        onResult = viewModel::installActivation,
    )

    LaunchedEffect(viewModel) {
        viewModel.events.collectLatest { event ->
            when (event) {
                is ActivationEvent.CreateRequestFile -> {
                    createRequestLauncher.launch(event.filename)
                }

                is ActivationEvent.Message -> {
                    snackbarHostState.showSnackbar(event.text)
                }
            }
        }
    }

    ActivationScreen(
        state = state,
        previousCrash = visibleCrash,
        snackbarHostState = snackbarHostState,
        onNationalCodeChanged = viewModel::updateNationalCode,
        onCreateRequest = viewModel::createRequest,
        onOpenActivation = {
            openActivationLauncher.launch(
                arrayOf(
                    "application/json",
                    "application/octet-stream",
                    "text/plain",
                    "*/*",
                ),
            )
        },
        onRefresh = viewModel::refreshStatus,
        onRetryInitialization = viewModel::retryInitialization,
        onClearPreviousCrash = {
            onClearPreviousCrash()
            visibleCrash = null
        },
    )
}

@Composable
private fun ActivationScreen(
    state: ActivationUiState,
    previousCrash: String?,
    snackbarHostState: SnackbarHostState,
    onNationalCodeChanged: (String) -> Unit,
    onCreateRequest: () -> Unit,
    onOpenActivation: () -> Unit,
    onRefresh: () -> Unit,
    onRetryInitialization: () -> Unit,
    onClearPreviousCrash: () -> Unit,
) {
    Scaffold(
        modifier = Modifier.fillMaxSize(),
        snackbarHost = {
            SnackbarHost(hostState = snackbarHostState)
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .statusBarsPadding()
                .navigationBarsPadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            HeaderCard()

            previousCrash?.let {
                DiagnosticCard(
                    title = "گزارش خطای اجرای قبلی",
                    text = it,
                    onDismiss = onClearPreviousCrash,
                )
            }

            state.fatalError?.let {
                DiagnosticCard(
                    title = "خطای راه‌اندازی فعال‌سازی",
                    text = it,
                    actionLabel = "تلاش دوباره",
                    onDismiss = onRetryInitialization,
                )
            }

            StatusCard(state = state)
            ActivationActionsCard(
                state = state,
                onNationalCodeChanged = onNationalCodeChanged,
                onCreateRequest = onCreateRequest,
                onOpenActivation = onOpenActivation,
            )

            OutlinedButton(
                onClick = onRefresh,
                modifier = Modifier.fillMaxWidth(),
                enabled = state.isReady && !state.isBusy,
            ) {
                Text("بازخوانی وضعیت مجوز")
            }

            Text(
                text = "فاز ۱ — فعال‌سازی مستقل Native Android",
                modifier = Modifier.fillMaxWidth(),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                fontSize = 12.sp,
            )
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

@Composable
private fun HeaderCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(18.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Image(
                painter = painterResource(R.drawable.javanrood_app),
                contentDescription = null,
                modifier = Modifier.size(76.dp),
                contentScale = ContentScale.Fit,
            )

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(5.dp),
            ) {
                Text(
                    text = "فرمانداری شهرستان جوانرود",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary,
                    textAlign = TextAlign.Right,
                )
                Text(
                    text = "سامانه همراه کمیته‌ها و بلوک‌های شهری",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Right,
                )
            }
        }
    }
}

@Composable
private fun DiagnosticCard(
    title: String,
    text: String,
    actionLabel: String = "پاک‌کردن گزارش",
    onDismiss: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.errorContainer,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(
                text = title,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onErrorContainer,
            )
            Text(
                text = text,
                color = MaterialTheme.colorScheme.onErrorContainer,
                fontSize = 12.sp,
            )
            OutlinedButton(
                onClick = onDismiss,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(actionLabel)
            }
        }
    }
}

@Composable
private fun StatusCard(
    state: ActivationUiState,
) {
    val status = state.status
    val statusTitle = when (status.state) {
        LicenseState.NOT_ACTIVATED -> "فعال‌سازی انجام نشده"
        LicenseState.VALID -> "مجوز فعال و معتبر"
        LicenseState.NOT_YET_VALID -> "مجوز هنوز شروع نشده"
        LicenseState.EXPIRED -> "اعتبار مجوز پایان یافته"
        LicenseState.BLOCKED -> "مجوز مسدود شده"
        LicenseState.CLOCK_ROLLBACK -> "اختلال در ساعت دستگاه"
        LicenseState.CORRUPTED -> "مجوز محلی یا فضای امن آسیب دیده"
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(9.dp),
        ) {
            Text(
                text = statusTitle,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = if (status.state == LicenseState.VALID) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.onSurface
                },
            )
            Text(
                text = status.message,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            status.payload?.let { license ->
                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 4.dp),
                )
                LicenseLine(
                    label = "مسئول",
                    value = license["responsible_full_name"]
                        ?.jsonPrimitive
                        ?.contentOrNull
                        .orEmpty(),
                )
                LicenseLine(
                    label = "بلوک",
                    value = license["zone_name"]
                        ?.jsonPrimitive
                        ?.contentOrNull
                        .orEmpty(),
                )
                LicenseLine(
                    label = "کمیته",
                    value = license["committee_title"]
                        ?.jsonPrimitive
                        ?.contentOrNull
                        .orEmpty(),
                )
                LicenseLine(
                    label = "پایان اعتبار",
                    value = license["valid_until"]
                        ?.jsonPrimitive
                        ?.contentOrNull
                        .orEmpty(),
                )
                status.remainingDays?.let {
                    LicenseLine(
                        label = "روز باقی‌مانده",
                        value = it.toString(),
                    )
                }
            }

            if (state.deviceId.isNotBlank()) {
                Text(
                    text = "شناسه دستگاه: …${state.deviceId.takeLast(12)}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Left,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }
    }
}

@Composable
private fun LicenseLine(
    label: String,
    value: String,
) {
    if (value.isBlank()) return

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text = label,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontSize = 13.sp,
        )
        Text(
            text = value,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.SemiBold,
            textAlign = TextAlign.Left,
        )
    }
}

@Composable
private fun ActivationActionsCard(
    state: ActivationUiState,
    onNationalCodeChanged: (String) -> Unit,
    onCreateRequest: () -> Unit,
    onOpenActivation: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = "فعال‌سازی یا تمدید",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )

            Text(
                text = "کد ملی مسئول را وارد کنید. ابتدا فایل درخواست .jrr را بسازید؛ سپس فایل .jra دریافتی از مدیر را انتخاب کنید.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            OutlinedTextField(
                value = state.nationalCode,
                onValueChange = onNationalCodeChanged,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("کد ملی ۱۰ رقمی") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Number,
                ),
                enabled = state.isReady && !state.isBusy,
            )

            Button(
                onClick = onCreateRequest,
                modifier = Modifier.fillMaxWidth(),
                enabled = state.isReady && !state.isBusy,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            ) {
                Text("ساخت و ذخیره فایل درخواست (.jrr)")
            }

            OutlinedButton(
                onClick = onOpenActivation,
                modifier = Modifier.fillMaxWidth(),
                enabled = state.isReady && !state.isBusy,
            ) {
                Text("انتخاب و نصب فایل فعال‌سازی (.jra)")
            }

            if (state.isBusy) {
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(30.dp),
                        strokeWidth = 3.dp,
                    )
                }
            }
        }
    }
}
