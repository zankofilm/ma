# -*- coding: utf-8 -*-
"""نسخه تشخیصی کلاینت اندروید جوانرود.

این نسخه ابتدا یک صفحه دیباگ پایدار باز می‌کند، سپس راه‌اندازی برنامه را
مرحله‌به‌مرحله انجام می‌دهد. هر Exception کامل روی صفحه نمایش داده و در
فایل javanrood_runtime_debug.txt ذخیره می‌شود.
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_LOG_LEVEL", "debug")
os.environ.setdefault("KIVY_LOG_ENABLE", "1")
os.environ.setdefault("KIVY_NO_FILELOG", "0")

_BOOTSTRAP_LOG = []


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _bootstrap_log(message: str) -> None:
    line = f"[{_timestamp()}] {message}"
    _BOOTSTRAP_LOG.append(line)
    print(line, flush=True)


def _candidate_log_paths() -> list[Path]:
    candidates: list[Path] = []

    android_private = os.environ.get("ANDROID_PRIVATE")
    if android_private:
        candidates.append(Path(android_private) / "javanrood_runtime_debug.txt")

    android_argument = os.environ.get("ANDROID_ARGUMENT")
    if android_argument:
        candidates.append(Path(android_argument) / "javanrood_runtime_debug.txt")

    candidates.append(SRC_DIR / "javanrood_runtime_debug.txt")
    return candidates


def _write_report(report: str) -> list[str]:
    saved: list[str] = []
    payload = (
        "JAVANROOD ANDROID RUNTIME DEBUG\n"
        f"Generated: {_timestamp()}\n"
        f"Python: {sys.version}\n"
        f"Platform: {sys.platform}\n\n"
        + report
    )

    for path in _candidate_log_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
            saved.append(str(path))
        except Exception:
            pass

    # Also try Android app-specific external storage. This does not require
    # broad storage permission and can be copied using ADB/file managers.
    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        external_dir = activity.getExternalFilesDir(None)
        if external_dir:
            external_path = (
                Path(str(external_dir.getAbsolutePath()))
                / "javanrood_runtime_debug.txt"
            )
            external_path.write_text(payload, encoding="utf-8")
            saved.append(str(external_path))
    except Exception:
        pass

    return list(dict.fromkeys(saved))


try:
    _bootstrap_log("در حال بارگذاری Kivy")
    from kivy.app import App
    from kivy.base import ExceptionHandler, ExceptionManager
    from kivy.clock import Clock
    from kivy.core.clipboard import Clipboard
    from kivy.core.text import LabelBase
    from kivy.core.window import Window
    from kivy.lang import Builder
    from kivy.metrics import dp
    from kivy.properties import StringProperty
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
    from kivy.uix.textinput import TextInput

    _bootstrap_log("Kivy با موفقیت بارگذاری شد")
except BaseException:
    report = "خطا در بارگذاری Kivy:\n\n" + traceback.format_exc()
    paths = _write_report(report)
    print(report, file=sys.stderr, flush=True)
    print("Saved paths:", paths, file=sys.stderr, flush=True)
    raise


_PROJECT_IMPORT_ERROR = ""
try:
    _bootstrap_log("در حال بارگذاری ماژول‌های داخلی پروژه")
    from client_exchange_core import ExchangeError
    from client_license_store import LicenseStore
    from jalali_utils import iso_to_jalali, to_persian_digits
    from rtl_text import fa
    from version import APP_NAME, APP_VERSION

    _bootstrap_log("همه ماژول‌های داخلی پروژه بارگذاری شدند")
except BaseException:
    _PROJECT_IMPORT_ERROR = traceback.format_exc()
    _bootstrap_log("بارگذاری ماژول‌های داخلی پروژه ناموفق بود")

    class ExchangeError(Exception):
        pass

    LicenseStore = None
    APP_NAME = "Javanrood Client DEBUG"
    APP_VERSION = "runtime-debug"

    def fa(value) -> str:
        return "" if value is None else str(value)

    def iso_to_jalali(value) -> str:
        return "" if value is None else str(value)

    def to_persian_digits(value) -> str:
        return "" if value is None else str(value)


FONT_NAME = "Vazirmatn"
DEBUG_BUILD_ID = "runtime-debug-20260729-01"


def _register_font() -> None:
    font_dir = SRC_DIR.parent / "assets" / "fonts"
    regular = font_dir / "Vazirmatn-Regular.ttf"
    bold = font_dir / "Vazirmatn-Bold.ttf"

    if not regular.exists():
        _bootstrap_log(f"فونت سفارشی پیدا نشد: {regular}")
        return

    LabelBase.register(
        name=FONT_NAME,
        fn_regular=str(regular),
        fn_bold=str(bold) if bold.exists() else str(regular),
    )
    _bootstrap_log(f"فونت ثبت شد: {regular}")


class DebugScreen(Screen):
    """صفحه‌ای که حتی در صورت شکست رابط اصلی، گزارش را نمایش می‌دهد."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
        )

        title = Label(
            text="Javanrood Runtime Debug",
            size_hint_y=None,
            height=dp(42),
            font_size="18sp",
        )
        root.add_widget(title)

        self.status_label = Label(
            text=f"Build: {DEBUG_BUILD_ID}",
            size_hint_y=None,
            height=dp(34),
            font_size="13sp",
        )
        root.add_widget(self.status_label)

        self.report_box = TextInput(
            text="\n".join(_BOOTSTRAP_LOG),
            readonly=True,
            multiline=True,
            font_size="12sp",
        )
        root.add_widget(self.report_box)

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        copy_button = Button(text="کپی گزارش")
        copy_button.bind(on_release=self.copy_report)
        buttons.add_widget(copy_button)

        retry_button = Button(text="تلاش دوباره")
        retry_button.bind(on_release=self.retry)
        buttons.add_widget(retry_button)

        root.add_widget(buttons)
        self.add_widget(root)

    def set_status(self, value: str) -> None:
        self.status_label.text = value

    def append(self, value: str) -> None:
        current = self.report_box.text.rstrip()
        self.report_box.text = f"{current}\n{value}".strip()
        self.report_box.cursor = (0, len(self.report_box._lines))

    def show_report(self, title: str, report: str) -> None:
        paths = _write_report(report)
        paths_text = "\n".join(f"Saved: {path}" for path in paths)
        full_report = f"{title}\n\n{report}"
        if paths_text:
            full_report += f"\n\n{paths_text}"

        self.set_status("خطا پیدا شد؛ گزارش زیر را ارسال کن")
        self.report_box.text = full_report

    def copy_report(self, *_args) -> None:
        try:
            Clipboard.copy(self.report_box.text)
            self.set_status("گزارش در کلیپ‌بورد کپی شد")
        except Exception as exc:
            self.set_status(f"کپی ناموفق بود: {exc}")

    def retry(self, *_args) -> None:
        app = App.get_running_app()
        if app is not None and hasattr(app, "start_real_application"):
            app.start_real_application()


class ActivationScreen(Screen):
    app_title = StringProperty(APP_NAME)
    status_text = StringProperty("")
    activation_path_display = StringProperty("")

    @staticmethod
    def rtl_text(value: str) -> str:
        """تابع RTL باید پیش از اعمال ruleهای KV در دسترس باشد."""
        return fa(value)

    def __init__(self, store: LicenseStore, **kwargs):
        self.store = store
        self._chosen_activation_path = ""
        super().__init__(**kwargs)
        self.activation_path_display = fa("هنوز فایلی انتخاب نشده است.")
        self.refresh_status()

    def refresh_status(self):
        try:
            result = self.store.validate(update_clock=False)
        except Exception as exc:
            self.status_text = fa(f"وضعیت مجوز محلی قابل خواندن نیست: {exc}")
            return
        lic = result.get("license") or {}
        if result["status"] == "not_activated":
            self.status_text = fa("این دستگاه هنوز فعال نشده است.")
            return
        expiry = iso_to_jalali(lic.get("valid_until"))
        self.status_text = fa(
            f"مسئول: {lic.get('responsible_full_name', '')}\n"
            f"بلوک: {lic.get('zone_name', '')} | کمیته: {lic.get('committee_title', '')}\n"
            f"پایان اعتبار: {expiry} | وضعیت: {result.get('message', '')}"
        )

    def create_request(self):
        from client_exchange_core import build_activation_request, normalize_national_code
        from client_runtime import data_dir

        code_field = self.ids.request_national_code
        try:
            code = normalize_national_code(code_field.text)
            out_path = str(data_dir() / "client_activation_request.jrr")
            build_activation_request(out_path, code, self.store.key_store, APP_VERSION)
            self._notify(
                fa("درخواست ساخته شد"),
                fa(f"فایل درخواست فعال‌سازی ساخته شد:\n{out_path}\nآن را به مدیر سامانه تحویل دهید."),
            )
        except ExchangeError as exc:
            self._notify(fa("خطا"), fa(str(exc)), error=True)
        except Exception as exc:  # noqa: BLE001
            self._notify(fa("خطای غیرمنتظره"), fa(str(exc)), error=True)

    def choose_activation_file(self):
        # TODO فاز ۲: انتخاب‌گر فایل بومی اندروید (پلاگین Storage Access
        # Framework از طریق pyjnius) به‌جای مسیر ثابت.
        from client_runtime import data_dir

        default_path = data_dir() / "incoming_activation.jra"
        self._chosen_activation_path = str(default_path)
        self.activation_path_display = fa(
            f"مسیر پیش‌فرض فایل فعال‌سازی:\n{default_path}\n"
            "فایل .jra دریافتی از مدیر را در همین مسیر قرار دهید."
        )

    def install_activation(self):
        code_field = self.ids.activation_national_code
        if not self._chosen_activation_path:
            self._notify(fa("فایل انتخاب نشده"), fa("ابتدا مسیر فایل فعال‌سازی را مشخص کنید."), error=True)
            return
        try:
            payload = self.store.install(self._chosen_activation_path, code_field.text)
            expiry = iso_to_jalali(payload.get("valid_until"))
            self._notify(
                fa("فعال‌سازی موفق"),
                fa(f"کلاینت برای {payload.get('responsible_full_name')} فعال شد.\nپایان اعتبار: {expiry}"),
            )
            self.refresh_status()
            self.manager.current = "login"
            self.manager.get_screen("login").refresh()
        except ExchangeError as exc:
            self._notify(fa("فعال‌سازی ناموفق"), fa(str(exc)), error=True)
        except Exception as exc:  # noqa: BLE001
            self._notify(fa("خطای غیرمنتظره"), fa(str(exc)), error=True)

    def _notify(self, title: str, message: str, error: bool = False):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label

        content = Label(text=message, halign="right", valign="middle")
        content.bind(size=lambda *_: setattr(content, "text_size", content.size))
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.5))
        popup.open()


class LoginScreen(Screen):
    app_title = StringProperty(APP_NAME)
    license_info_text = StringProperty("")

    @staticmethod
    def rtl_text(value: str) -> str:
        """تابع RTL باید پیش از اعمال ruleهای KV در دسترس باشد."""
        return fa(value)

    def __init__(self, store: LicenseStore, **kwargs):
        self.store = store
        super().__init__(**kwargs)
        self.refresh()

    def refresh(self):
        result = self.store.validate(update_clock=False)
        lic = result.get("license") or {}
        if "username_input" in self.ids:
            self.ids.username_input.text = str(lic.get("username") or "")
        expiry = iso_to_jalali(lic.get("valid_until"))
        remaining = result.get("remaining_days")
        remain_text = f" | {to_persian_digits(remaining)} روز باقی‌مانده" if remaining is not None else ""
        self.license_info_text = fa(
            f"مسئول: {lic.get('responsible_full_name', '')}\n"
            f"بلوک: {lic.get('zone_name', '')}\n"
            f"دسترسی: {lic.get('committee_title', '')}\n"
            f"پایان اعتبار: {expiry}{remain_text}\n"
            f"وضعیت: {result.get('message', '')}"
        )

    def login(self):
        result = self.store.validate(update_clock=True)
        if result["status"] != "valid":
            self._notify(fa("ورود غیرممکن"), fa(result["message"]), error=True)
            return
        username = self.ids.username_input.text
        password = self.ids.password_input.text
        if not self.store.authenticate(username, password):
            self._notify(fa("ورود ناموفق"), fa("نام کاربری یا رمز عبور صحیح نیست."), error=True)
            return
        # TODO فاز ۲: انتقال به ClientMainScreen با پنل‌های اعضا/جلسات/...
        self._notify(fa("ورود موفق"), fa("ورود با موفقیت انجام شد. صفحه اصلی در فاز بعدی افزوده می‌شود."))

    def go_to_activation(self):
        self.manager.current = "activation"
        self.manager.get_screen("activation").refresh_status()

    def _notify(self, title: str, message: str, error: bool = False):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label

        content = Label(text=message, halign="right", valign="middle")
        content.bind(size=lambda *_: setattr(content, "text_size", content.size))
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.5))
        popup.open()


class _RuntimeExceptionHandler(ExceptionHandler):
    def handle_exception(self, exception):
        report = "خطای زمان اجرای Kivy:\n\n" + "".join(
            traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__,
            )
        )
        app = App.get_running_app()
        if app is not None and hasattr(app, "show_fatal_report"):
            Clock.schedule_once(
                lambda _dt: app.show_fatal_report(
                    "خطای زمان اجرای Kivy",
                    report,
                ),
                0,
            )
            return ExceptionManager.PASS
        _write_report(report)
        return ExceptionManager.RAISE


class JavanroodClientApp(App):
    title = "Javanrood Client Runtime Debug"

    def build(self):
        Window.clearcolor = (0.07, 0.09, 0.13, 1)

        self.manager = ScreenManager(transition=NoTransition())
        self.debug_screen = DebugScreen(name="runtime_debug")
        self.manager.add_widget(self.debug_screen)
        self.manager.current = "runtime_debug"

        self._kv_loaded = False
        self._initializing = False
        self.store = None
        return self.manager

    def on_start(self):
        ExceptionManager.add_handler(_RuntimeExceptionHandler())
        self._install_exception_hooks()
        Clock.schedule_once(lambda _dt: self.start_real_application(), 0.25)

    def _install_exception_hooks(self) -> None:
        def sys_hook(exc_type, exc_value, exc_tb):
            report = "خطای عمومی Python:\n\n" + "".join(
                traceback.format_exception(exc_type, exc_value, exc_tb)
            )
            _write_report(report)
            Clock.schedule_once(
                lambda _dt: self.show_fatal_report(
                    "خطای عمومی Python",
                    report,
                ),
                0,
            )

        def thread_hook(args):
            report = "خطای Thread:\n\n" + "".join(
                traceback.format_exception(
                    args.exc_type,
                    args.exc_value,
                    args.exc_traceback,
                )
            )
            _write_report(report)
            Clock.schedule_once(
                lambda _dt: self.show_fatal_report(
                    "خطای Thread",
                    report,
                ),
                0,
            )

        sys.excepthook = sys_hook
        if hasattr(threading, "excepthook"):
            threading.excepthook = thread_hook

    def debug_step(self, message: str) -> None:
        line = f"[{_timestamp()}] {message}"
        print(line, flush=True)
        self.debug_screen.append(line)
        self.debug_screen.set_status(message)

    def show_fatal_report(self, title: str, report: str) -> None:
        self.manager.current = "runtime_debug"
        self.debug_screen.show_report(title, report)

    def start_real_application(self) -> None:
        if self._initializing:
            return

        self._initializing = True
        self.manager.current = "runtime_debug"
        self.debug_screen.report_box.text = "\n".join(_BOOTSTRAP_LOG)

        try:
            self.debug_step("مرحله ۱: بررسی importهای پروژه")
            if _PROJECT_IMPORT_ERROR:
                raise RuntimeError(
                    "یکی از ماژول‌های داخلی پروژه import نشد.\n\n"
                    + _PROJECT_IMPORT_ERROR
                )
            if LicenseStore is None:
                raise RuntimeError("LicenseStore در دسترس نیست.")

            self.debug_step("مرحله ۲: ثبت فونت")
            _register_font()

            self.debug_step("مرحله ۳: بارگذاری فایل KV")
            kv_path = SRC_DIR / "javanrood.kv"
            if not kv_path.exists():
                raise FileNotFoundError(f"فایل KV پیدا نشد: {kv_path}")

            if not self._kv_loaded:
                Builder.load_file(str(kv_path))
                self._kv_loaded = True

            self.debug_step("مرحله ۴: ساخت LicenseStore")
            self.store = LicenseStore()

            self.debug_step("مرحله ۵: ساخت صفحه فعال‌سازی")
            activation_screen = ActivationScreen(
                self.store,
                name="activation",
            )

            self.debug_step("مرحله ۶: ساخت صفحه ورود")
            login_screen = LoginScreen(
                self.store,
                name="login",
            )

            for screen_name in ("activation", "login"):
                if self.manager.has_screen(screen_name):
                    self.manager.remove_widget(
                        self.manager.get_screen(screen_name)
                    )

            self.manager.add_widget(activation_screen)
            self.manager.add_widget(login_screen)

            self.debug_step("مرحله ۷: اعتبارسنجی مجوز")
            result = self.store.validate(update_clock=False)
            status = result.get("status")

            self.debug_step(
                f"مرحله ۸: رابط اصلی آماده شد؛ وضعیت مجوز: {status}"
            )
            self.manager.current = (
                "login" if status != "not_activated" else "activation"
            )

        except BaseException:
            report = traceback.format_exc()
            self.show_fatal_report("خطای راه‌اندازی برنامه", report)
        finally:
            self._initializing = False


def main() -> int:
    try:
        JavanroodClientApp().run()
        return 0
    except BaseException:
        report = "کرش نهایی خارج از EventLoop:\n\n" + traceback.format_exc()
        paths = _write_report(report)
        print(report, file=sys.stderr, flush=True)
        print("Saved paths:", paths, file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
