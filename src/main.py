# -*- coding: utf-8 -*-
"""کلاینت اندروید جوانرود ـ راه‌انداز پاک و مرحله‌ای.

اصول این ورودی:
1) رابط تشخیص خطا قبل از import ماژول‌های پروژه نمایش داده می‌شود.
2) هر مرحله قبل از اجرا در حافظه خصوصی برنامه ثبت می‌شود.
3) اگر یک کتابخانه native باعث بسته‌شدن ناگهانی شود، اجرای بعدی آخرین
   مرحله نیمه‌تمام را نمایش می‌دهد.
4) هیچ فایل Python جدیدی برای اجرای اصلی لازم نیست؛ ورودی همچنان main.py است.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

BUILD_ID = "20260730-full-audit-clean-01"
SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_LOG_LEVEL", "debug")
os.environ.setdefault("KIVY_LOG_ENABLE", "1")
os.environ.setdefault("KIVY_NO_FILELOG", "0")

print(f"JAVANROOD_BOOT: main.py reached | build={BUILD_ID}", flush=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _private_root() -> Path:
    for env_name in ("ANDROID_PRIVATE", "ANDROID_ARGUMENT"):
        value = os.environ.get(env_name)
        if value:
            path = Path(value)
            try:
                path.mkdir(parents=True, exist_ok=True)
                return path
            except Exception:
                pass

    fallback = SRC_DIR
    try:
        fallback.mkdir(parents=True, exist_ok=True)
    except Exception:
        fallback = Path.cwd()
    return fallback


STAGE_PATH = _private_root() / "javanrood_startup_stage.json"
REPORT_PATH = _private_root() / "javanrood_runtime_debug.txt"


def _read_previous_stage() -> dict[str, Any]:
    try:
        if STAGE_PATH.exists():
            value = json.loads(STAGE_PATH.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
    except Exception:
        pass
    return {}


PREVIOUS_STAGE = _read_previous_stage()


def _write_stage(stage: str, state: str = "running", detail: str = "") -> None:
    payload = {
        "build_id": BUILD_ID,
        "timestamp": _timestamp(),
        "stage": stage,
        "state": state,
        "detail": detail,
    }
    try:
        STAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STAGE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass
    print(
        f"JAVANROOD_STAGE: {stage} | state={state} | {detail}",
        flush=True,
    )


def _format_previous_stage() -> str:
    if not PREVIOUS_STAGE:
        return "No previous startup record."

    return (
        "Previous run:\n"
        f"Build: {PREVIOUS_STAGE.get('build_id', '-')}\n"
        f"Stage: {PREVIOUS_STAGE.get('stage', '-')}\n"
        f"State: {PREVIOUS_STAGE.get('state', '-')}\n"
        f"Time: {PREVIOUS_STAGE.get('timestamp', '-')}\n"
        f"Detail: {PREVIOUS_STAGE.get('detail', '-')}"
    )


def _write_report(title: str, report: str) -> list[str]:
    text = (
        "JAVANROOD ANDROID RUNTIME REPORT\n"
        f"Build: {BUILD_ID}\n"
        f"Generated: {_timestamp()}\n"
        f"Python: {sys.version}\n"
        f"Platform: {sys.platform}\n\n"
        f"{title}\n\n{report}\n\n"
        f"{_format_previous_stage()}\n"
    )

    saved_paths: list[str] = []
    for path in (REPORT_PATH, SRC_DIR / "javanrood_runtime_debug.txt"):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            saved_paths.append(str(path))
        except Exception:
            pass

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
            external_path.write_text(text, encoding="utf-8")
            saved_paths.append(str(external_path))
    except Exception:
        pass

    return list(dict.fromkeys(saved_paths))


_write_stage("before_kivy_import")

try:
    from kivy.app import App
    from kivy.base import ExceptionHandler, ExceptionManager
    from kivy.clock import Clock
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
except BaseException:
    _write_stage(
        "kivy_import",
        "failed",
        traceback.format_exc()[-2000:],
    )
    _write_report("Kivy import failed", traceback.format_exc())
    raise

_write_stage("kivy_import", "complete")

# مقادیر موقت تا زمان import مرحله‌ای ماژول‌های پروژه.
class ExchangeError(ValueError):
    pass


LicenseStore: Any = None
APP_NAME = "Javanrood Client Clean"
APP_VERSION = "1.2.0"


def fa(value: Any) -> str:
    return "" if value is None else str(value)


def iso_to_jalali(value: Any) -> str:
    return "" if value is None else str(value)


def to_persian_digits(value: Any) -> str:
    return "" if value is None else str(value)


FONT_NAME = "Vazirmatn"


def _register_font() -> None:
    font_dir = SRC_DIR.parent / "assets" / "fonts"
    regular = font_dir / "Vazirmatn-Regular.ttf"
    bold = font_dir / "Vazirmatn-Bold.ttf"

    if not regular.exists():
        print(f"JAVANROOD_FONT: optional font not found: {regular}", flush=True)
        return

    LabelBase.register(
        name=FONT_NAME,
        fn_regular=str(regular),
        fn_bold=str(bold) if bold.exists() else str(regular),
    )


class BootstrapScreen(Screen):
    """صفحه‌ای که فقط به Kivy وابسته است و همیشه اول ساخته می‌شود."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
        )

        root.add_widget(
            Label(
                text="Javanrood Clean Startup",
                size_hint_y=None,
                height=dp(42),
                font_size="18sp",
            )
        )

        self.status_label = Label(
            text=f"Build: {BUILD_ID}",
            size_hint_y=None,
            height=dp(38),
            font_size="13sp",
        )
        root.add_widget(self.status_label)

        previous_text = _format_previous_stage()
        if (
            PREVIOUS_STAGE
            and PREVIOUS_STAGE.get("state") == "running"
            and PREVIOUS_STAGE.get("build_id") == BUILD_ID
        ):
            previous_text = (
                "اجرای قبلی در این مرحله ناگهانی متوقف شده است:\n\n"
                + previous_text
            )

        self.report_box = TextInput(
            text=previous_text,
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
        self.report_box.scroll_y = 0

    def show_report(self, title: str, report: str) -> None:
        paths = _write_report(title, report)
        path_text = "\n".join(f"Saved: {path}" for path in paths)
        self.report_box.text = f"{title}\n\n{report}"
        if path_text:
            self.report_box.text += f"\n\n{path_text}"
        self.set_status("خطا پیدا شد؛ متن گزارش را ارسال کن")

    def copy_report(self, *_args) -> None:
        try:
            from kivy.core.clipboard import Clipboard

            Clipboard.copy(self.report_box.text)
            self.set_status("گزارش کپی شد")
        except Exception as exc:
            self.set_status(f"کپی ناموفق: {exc}")

    def retry(self, *_args) -> None:
        app = App.get_running_app()
        if app is not None:
            app.start_real_application()


class ActivationScreen(Screen):
    app_title = StringProperty(APP_NAME)
    status_text = StringProperty("")
    activation_path_display = StringProperty("")

    @staticmethod
    def rtl_text(value: str) -> str:
        return fa(value)

    def __init__(self, store, **kwargs):
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
        if result.get("status") == "not_activated":
            self.status_text = fa("این دستگاه هنوز فعال نشده است.")
            return

        expiry = iso_to_jalali(lic.get("valid_until"))
        self.status_text = fa(
            f"مسئول: {lic.get('responsible_full_name', '')}\n"
            f"بلوک: {lic.get('zone_name', '')} | "
            f"کمیته: {lic.get('committee_title', '')}\n"
            f"پایان اعتبار: {expiry} | "
            f"وضعیت: {result.get('message', '')}"
        )

    def create_request(self):
        from client_exchange_core import (
            build_activation_request,
            normalize_national_code,
        )
        from client_runtime import data_dir

        code_field = self.ids.request_national_code
        try:
            code = normalize_national_code(code_field.text)
            out_path = str(data_dir() / "client_activation_request.jrr")
            build_activation_request(
                out_path,
                code,
                self.store.key_store,
                APP_VERSION,
            )
            self._notify(
                fa("درخواست ساخته شد"),
                fa(
                    "فایل درخواست فعال‌سازی ساخته شد:\n"
                    f"{out_path}\n"
                    "آن را به مدیر سامانه تحویل دهید."
                ),
            )
        except ExchangeError as exc:
            self._notify(fa("خطا"), fa(str(exc)), error=True)
        except Exception:
            self._notify(
                fa("خطای غیرمنتظره"),
                fa(traceback.format_exc()),
                error=True,
            )

    def choose_activation_file(self):
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
            self._notify(
                fa("فایل انتخاب نشده"),
                fa("ابتدا مسیر فایل فعال‌سازی را مشخص کنید."),
                error=True,
            )
            return

        try:
            payload = self.store.install(
                self._chosen_activation_path,
                code_field.text,
            )
            expiry = iso_to_jalali(payload.get("valid_until"))
            self._notify(
                fa("فعال‌سازی موفق"),
                fa(
                    f"کلاینت برای "
                    f"{payload.get('responsible_full_name')} فعال شد.\n"
                    f"پایان اعتبار: {expiry}"
                ),
            )
            self.refresh_status()
            self.manager.current = "login"
            self.manager.get_screen("login").refresh()
        except ExchangeError as exc:
            self._notify(
                fa("فعال‌سازی ناموفق"),
                fa(str(exc)),
                error=True,
            )
        except Exception:
            self._notify(
                fa("خطای غیرمنتظره"),
                fa(traceback.format_exc()),
                error=True,
            )

    def _notify(self, title: str, message: str, error: bool = False):
        from kivy.uix.popup import Popup

        content = Label(
            text=message,
            halign="right",
            valign="middle",
        )
        content.bind(
            size=lambda *_: setattr(content, "text_size", content.size)
        )
        Popup(
            title=title,
            content=content,
            size_hint=(0.88, 0.58),
        ).open()


class LoginScreen(Screen):
    app_title = StringProperty(APP_NAME)
    license_info_text = StringProperty("")

    @staticmethod
    def rtl_text(value: str) -> str:
        return fa(value)

    def __init__(self, store, **kwargs):
        self.store = store
        super().__init__(**kwargs)
        self.refresh()

    def refresh(self):
        try:
            result = self.store.validate(update_clock=False)
        except Exception:
            self.license_info_text = fa(traceback.format_exc())
            return

        lic = result.get("license") or {}
        if "username_input" in self.ids:
            self.ids.username_input.text = str(lic.get("username") or "")

        expiry = iso_to_jalali(lic.get("valid_until"))
        remaining = result.get("remaining_days")
        remain_text = (
            f" | {to_persian_digits(remaining)} روز باقی‌مانده"
            if remaining is not None
            else ""
        )
        self.license_info_text = fa(
            f"مسئول: {lic.get('responsible_full_name', '')}\n"
            f"بلوک: {lic.get('zone_name', '')}\n"
            f"دسترسی: {lic.get('committee_title', '')}\n"
            f"پایان اعتبار: {expiry}{remain_text}\n"
            f"وضعیت: {result.get('message', '')}"
        )

    def login(self):
        try:
            result = self.store.validate(update_clock=True)
            if result.get("status") != "valid":
                self._notify(
                    fa("ورود غیرممکن"),
                    fa(result.get("message", "")),
                    error=True,
                )
                return

            username = self.ids.username_input.text
            password = self.ids.password_input.text
            if not self.store.authenticate(username, password):
                self._notify(
                    fa("ورود ناموفق"),
                    fa("نام کاربری یا رمز عبور صحیح نیست."),
                    error=True,
                )
                return

            self._notify(
                fa("ورود موفق"),
                fa(
                    "ورود با موفقیت انجام شد. "
                    "صفحه اصلی در فاز بعدی افزوده می‌شود."
                ),
            )
        except Exception:
            self._notify(
                fa("خطای ورود"),
                fa(traceback.format_exc()),
                error=True,
            )

    def go_to_activation(self):
        self.manager.current = "activation"
        self.manager.get_screen("activation").refresh_status()

    def _notify(self, title: str, message: str, error: bool = False):
        from kivy.uix.popup import Popup

        content = Label(
            text=message,
            halign="right",
            valign="middle",
        )
        content.bind(
            size=lambda *_: setattr(content, "text_size", content.size)
        )
        Popup(
            title=title,
            content=content,
            size_hint=(0.88, 0.58),
        ).open()


class RuntimeExceptionHandler(ExceptionHandler):
    def handle_exception(self, exception):
        report = "".join(
            traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__,
            )
        )
        _write_stage(
            "kivy_event_loop",
            "failed",
            str(exception),
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

        _write_report("خطای زمان اجرای Kivy", report)
        return ExceptionManager.RAISE


class JavanroodClientApp(App):
    title = "Javanrood Client Clean"

    def build(self):
        Window.clearcolor = (0.07, 0.09, 0.13, 1)

        self.manager = ScreenManager(transition=NoTransition())
        self.bootstrap_screen = BootstrapScreen(name="bootstrap")
        self.manager.add_widget(self.bootstrap_screen)
        self.manager.current = "bootstrap"

        self._initializing = False
        self._kv_loaded = False
        self.store = None
        return self.manager

    def on_start(self):
        ExceptionManager.add_handler(RuntimeExceptionHandler())
        self._install_exception_hooks()
        Clock.schedule_once(
            lambda _dt: self.start_real_application(),
            0.35,
        )

    def _install_exception_hooks(self) -> None:
        def sys_hook(exc_type, exc_value, exc_tb):
            report = "".join(
                traceback.format_exception(
                    exc_type,
                    exc_value,
                    exc_tb,
                )
            )
            _write_stage(
                "python_uncaught_exception",
                "failed",
                str(exc_value),
            )
            _write_report("خطای عمومی Python", report)
            try:
                Clock.schedule_once(
                    lambda _dt: self.show_fatal_report(
                        "خطای عمومی Python",
                        report,
                    ),
                    0,
                )
            except Exception:
                pass

        def thread_hook(args):
            report = "".join(
                traceback.format_exception(
                    args.exc_type,
                    args.exc_value,
                    args.exc_traceback,
                )
            )
            _write_stage(
                "thread_exception",
                "failed",
                str(args.exc_value),
            )
            _write_report("خطای Thread", report)

        sys.excepthook = sys_hook
        if hasattr(threading, "excepthook"):
            threading.excepthook = thread_hook

    def debug_step(self, stage: str, text: str) -> None:
        _write_stage(stage, "running", text)
        line = f"[{_timestamp()}] {text}"
        self.bootstrap_screen.append(line)
        self.bootstrap_screen.set_status(text)

    def show_fatal_report(self, title: str, report: str) -> None:
        self.manager.current = "bootstrap"
        self.bootstrap_screen.show_report(title, report)

    def _load_project_modules(self) -> None:
        global ExchangeError
        global LicenseStore
        global APP_NAME
        global APP_VERSION
        global fa
        global iso_to_jalali
        global to_persian_digits

        checks = (
            ("import_filetype", "filetype"),
            ("import_arabic_reshaper", "arabic_reshaper"),
            ("import_python_bidi", "bidi.algorithm"),
            ("import_cryptography", "cryptography"),
            ("import_client_exchange_core", "client_exchange_core"),
            ("import_client_runtime", "client_runtime"),
            ("import_client_license_store", "client_license_store"),
            ("import_jalali_utils", "jalali_utils"),
            ("import_rtl_text", "rtl_text"),
            ("import_version", "version"),
        )

        loaded: dict[str, Any] = {}
        for stage, module_name in checks:
            self.debug_step(stage, f"در حال بارگذاری {module_name}")
            loaded[module_name] = importlib.import_module(module_name)
            _write_stage(stage, "complete", module_name)

        ExchangeError = loaded["client_exchange_core"].ExchangeError
        LicenseStore = loaded["client_license_store"].LicenseStore
        iso_to_jalali = loaded["jalali_utils"].iso_to_jalali
        to_persian_digits = loaded["jalali_utils"].to_persian_digits
        fa = loaded["rtl_text"].fa
        APP_NAME = loaded["version"].APP_NAME
        APP_VERSION = loaded["version"].APP_VERSION

    def _write_smoke_marker(self) -> None:
        marker = os.environ.get("JAVANROOD_SMOKE_MARKER")
        if marker:
            Path(marker).write_text(
                f"OK|{BUILD_ID}|{_timestamp()}",
                encoding="utf-8",
            )

    def start_real_application(self) -> None:
        if self._initializing:
            return

        self._initializing = True
        self.manager.current = "bootstrap"

        try:
            self.debug_step(
                "bootstrap_ui_ready",
                f"رابط اولیه آماده است ـ Build {BUILD_ID}",
            )

            self._load_project_modules()

            self.debug_step("register_font", "بررسی و ثبت فونت")
            _register_font()
            _write_stage("register_font", "complete")

            self.debug_step("load_kv", "بارگذاری فایل رابط javanrood.kv")
            kv_path = SRC_DIR / "javanrood.kv"
            if not kv_path.exists():
                raise FileNotFoundError(
                    f"فایل رابط پیدا نشد: {kv_path}"
                )

            if not self._kv_loaded:
                Builder.load_file(str(kv_path))
                self._kv_loaded = True
            _write_stage("load_kv", "complete", str(kv_path))

            self.debug_step(
                "create_license_store",
                "ساخت فضای امن مجوز",
            )
            self.store = LicenseStore()
            _write_stage("create_license_store", "complete")

            self.debug_step(
                "create_activation_screen",
                "ساخت صفحه فعال‌سازی",
            )
            activation_screen = ActivationScreen(
                self.store,
                name="activation",
            )
            activation_screen.app_title = APP_NAME
            _write_stage("create_activation_screen", "complete")

            self.debug_step(
                "create_login_screen",
                "ساخت صفحه ورود",
            )
            login_screen = LoginScreen(
                self.store,
                name="login",
            )
            login_screen.app_title = APP_NAME
            _write_stage("create_login_screen", "complete")

            for name in ("activation", "login"):
                if self.manager.has_screen(name):
                    self.manager.remove_widget(
                        self.manager.get_screen(name)
                    )

            self.manager.add_widget(activation_screen)
            self.manager.add_widget(login_screen)

            self.debug_step(
                "validate_license",
                "اعتبارسنجی مجوز محلی",
            )
            result = self.store.validate(update_clock=False)
            status = result.get("status")
            _write_stage(
                "validate_license",
                "complete",
                str(status),
            )

            self.manager.current = (
                "login"
                if status != "not_activated"
                else "activation"
            )

            _write_stage(
                "application_ready",
                "complete",
                f"screen={self.manager.current}",
            )
            self._write_smoke_marker()

            if os.environ.get("JAVANROOD_SMOKE_TEST") == "1":
                Clock.schedule_once(lambda _dt: self.stop(), 0.3)

        except BaseException:
            report = traceback.format_exc()
            _write_stage(
                "startup_failed",
                "failed",
                report[-2000:],
            )
            self.show_fatal_report(
                "خطای راه‌اندازی برنامه",
                report,
            )

            if os.environ.get("JAVANROOD_SMOKE_TEST") == "1":
                Clock.schedule_once(lambda _dt: self.stop(), 0.3)
        finally:
            self._initializing = False


def main() -> int:
    try:
        JavanroodClientApp().run()
        return 0
    except BaseException:
        report = traceback.format_exc()
        _write_stage(
            "outside_event_loop",
            "failed",
            report[-2000:],
        )
        _write_report(
            "کرش خارج از EventLoop",
            report,
        )
        print(report, file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
