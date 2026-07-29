# -*- coding: utf-8 -*-
"""کلاینت اندروید کمیته‌های محلات جوانرود.

فاز ۱: اسکلت برنامه با Kivy برای تأیید صحت زیرساخت build (Buildozer/
python-for-android) روی GitHub Actions، همراه با منطق واقعی مجوز
(LicenseStore) به‌جای نسخه آزمایشی. صفحات مدیریت اعضا/جلسات/مسائل/
مصوبات/اقدامات در فازهای بعدی افزوده می‌شوند.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition

from client_exchange_core import ExchangeError
from client_license_store import LicenseStore
from jalali_utils import iso_to_jalali, to_persian_digits
from rtl_text import fa
from version import APP_NAME, APP_VERSION

FONT_NAME = "Vazirmatn"


def _register_font():
    """در صورت وجود فونت وزیرمتن در assets، آن را به Kivy معرفی می‌کند."""
    font_dir = SRC_DIR.parent / "assets" / "fonts"
    regular = font_dir / "Vazirmatn-Regular.ttf"
    bold = font_dir / "Vazirmatn-Bold.ttf"
    if regular.exists():
        LabelBase.register(
            name=FONT_NAME,
            fn_regular=str(regular),
            fn_bold=str(bold) if bold.exists() else str(regular),
        )
        from kivy.config import Config
        Config.set("kivy", "default_font", [FONT_NAME, str(regular), str(bold if bold.exists() else regular), str(regular), str(regular)])


class ActivationScreen(Screen):
    app_title = StringProperty(APP_NAME)
    status_text = StringProperty("")
    activation_path_display = StringProperty("")

    def __init__(self, store: LicenseStore, **kwargs):
        self.store = store
        self._chosen_activation_path = ""
        super().__init__(**kwargs)
        self.rtl_text = fa
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

    def __init__(self, store: LicenseStore, **kwargs):
        self.store = store
        super().__init__(**kwargs)
        self.rtl_text = fa
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


class JavanroodClientApp(App):
    def build(self):
        _register_font()
        Window.clearcolor = (1, 1, 1, 1)
        Builder.load_file(str(SRC_DIR / "javanrood.kv"))

        self.store = LicenseStore()

        sm = ScreenManager(transition=NoTransition())
        activation_screen = ActivationScreen(self.store, name="activation")
        login_screen = LoginScreen(self.store, name="login")
        sm.add_widget(activation_screen)
        sm.add_widget(login_screen)

        result = self.store.validate(update_clock=False)
        sm.current = "login" if result["status"] != "not_activated" else "activation"
        return sm


def main() -> int:
    JavanroodClientApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
