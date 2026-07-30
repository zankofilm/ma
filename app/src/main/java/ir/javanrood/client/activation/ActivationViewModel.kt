package ir.javanrood.client.activation

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext


data class ActivationUiState(
    val nationalCode: String = "",
    val isBusy: Boolean = false,
    val isReady: Boolean = false,
    val fatalError: String? = null,
    val status: LicenseStatus = LicenseStatus(
        state = LicenseState.NOT_ACTIVATED,
        message = "در حال آماده‌سازی بخش فعال‌سازی...",
    ),
    val deviceId: String = "",
)

sealed interface ActivationEvent {
    data class CreateRequestFile(
        val filename: String,
    ) : ActivationEvent

    data class Message(
        val text: String,
    ) : ActivationEvent
}

class ActivationViewModel(
    application: Application,
) : AndroidViewModel(application) {
    private var repository: ActivationRepository? = null

    private val _state = MutableStateFlow(ActivationUiState())
    val state: StateFlow<ActivationUiState> = _state.asStateFlow()

    private val _events = Channel<ActivationEvent>(
        capacity = Channel.BUFFERED,
    )
    val events = _events.receiveAsFlow()

    private var pendingRequest: RequestDocument? = null

    init {
        initializeRepository()
    }

    fun updateNationalCode(value: String) {
        _state.value = _state.value.copy(
            nationalCode = value.take(16),
        )
    }

    fun createRequest() {
        if (_state.value.isBusy || !_state.value.isReady) return

        viewModelScope.launch {
            setBusy(true)
            try {
                val document = withContext(Dispatchers.IO) {
                    requireRepository().buildRequest(
                        nationalCode = _state.value.nationalCode,
                    )
                }
                pendingRequest = document
                _events.send(
                    ActivationEvent.CreateRequestFile(
                        filename = document.filename,
                    ),
                )
            } catch (error: Throwable) {
                report(error, "ساخت درخواست فعال‌سازی ناموفق بود.")
            } finally {
                setBusy(false)
            }
        }
    }

    fun savePreparedRequest(uri: Uri?) {
        if (uri == null) {
            pendingRequest = null
            return
        }

        val document = pendingRequest ?: return
        viewModelScope.launch {
            setBusy(true)
            try {
                withContext(Dispatchers.IO) {
                    requireRepository().writeRequest(uri, document)
                }
                _events.send(
                    ActivationEvent.Message(
                        "فایل درخواست فعال‌سازی با موفقیت ذخیره شد.",
                    ),
                )
            } catch (error: Throwable) {
                report(error, "ذخیره فایل درخواست ناموفق بود.")
            } finally {
                pendingRequest = null
                setBusy(false)
            }
        }
    }

    fun installActivation(uri: Uri?) {
        if (
            uri == null ||
            _state.value.isBusy ||
            !_state.value.isReady
        ) return

        viewModelScope.launch {
            setBusy(true)
            try {
                withContext(Dispatchers.IO) {
                    requireRepository().installActivation(
                        uri = uri,
                        nationalCode = _state.value.nationalCode,
                    )
                }

                refreshStatusInternal()
                _events.send(
                    ActivationEvent.Message(
                        "فعال‌سازی یا تمدید با موفقیت نصب شد.",
                    ),
                )
            } catch (error: Throwable) {
                report(error, "نصب فایل فعال‌سازی ناموفق بود.")
            } finally {
                setBusy(false)
            }
        }
    }

    fun refreshStatus() {
        if (_state.value.isBusy) return
        viewModelScope.launch {
            setBusy(true)
            try {
                withContext(Dispatchers.IO) {
                    refreshStatusInternal()
                }
            } catch (error: Throwable) {
                report(error, "بازخوانی وضعیت مجوز ناموفق بود.")
            } finally {
                setBusy(false)
            }
        }
    }

    fun retryInitialization() {
        if (_state.value.isBusy) return
        initializeRepository()
    }

    private fun initializeRepository() {
        viewModelScope.launch {
            setBusy(true)
            _state.value = _state.value.copy(
                fatalError = null,
                isReady = false,
                status = LicenseStatus(
                    state = LicenseState.NOT_ACTIVATED,
                    message = "در حال آماده‌سازی فضای امن برنامه...",
                ),
            )

            try {
                val created = withContext(Dispatchers.IO) {
                    ActivationRepository(getApplication())
                }
                repository = created
                val deviceId = withContext(Dispatchers.IO) {
                    created.deviceId
                }
                val status = withContext(Dispatchers.IO) {
                    created.status()
                }
                _state.value = _state.value.copy(
                    isReady = true,
                    fatalError = null,
                    deviceId = deviceId,
                    status = status,
                )
            } catch (error: Throwable) {
                repository = null
                _state.value = _state.value.copy(
                    isReady = false,
                    fatalError = error.toUserMessage(
                        "راه‌اندازی بخش فعال‌سازی ناموفق بود.",
                    ),
                    status = LicenseStatus(
                        state = LicenseState.CORRUPTED,
                        message = "بخش امن برنامه آماده نشد.",
                    ),
                )
            } finally {
                setBusy(false)
            }
        }
    }

    private fun refreshStatusInternal() {
        val current = requireRepository()
        _state.value = _state.value.copy(
            status = current.status(),
            deviceId = current.deviceId,
            isReady = true,
            fatalError = null,
        )
    }

    private suspend fun report(
        error: Throwable,
        fallback: String,
    ) {
        _events.send(
            ActivationEvent.Message(
                error.toUserMessage(fallback),
            ),
        )
    }

    private fun requireRepository(): ActivationRepository =
        repository ?: throw ActivationException(
            "بخش فعال‌سازی هنوز آماده نشده است.",
        )

    private fun setBusy(value: Boolean) {
        _state.value = _state.value.copy(isBusy = value)
    }
}

private fun Throwable.toUserMessage(fallback: String): String {
    val root = generateSequence(this) { it.cause }.last()
    val detail = root.message?.trim().orEmpty()
    return if (detail.isBlank()) fallback else "$fallback\n$detail"
}
