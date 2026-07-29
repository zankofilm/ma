# -*- coding: utf-8 -*-
"""ورودی ایمن برنامه اندروید.

هر خطای شروع برنامه در Logcat چاپ می‌شود و، در صورت سالم بودن Kivy،
روی یک صفحه تشخیصی قابل کپی نمایش داده می‌شود تا برنامه بدون پیام بسته نشود.
"""
from __future__ import annotations

import sys
import traceback


def _run_diagnostic_screen(report: str) -> None:
    from kivy.app import App
    from kivy.core.clipboard import Clipboard
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView

    class CrashReportApp(App):
        title = "Javanrood Client - Startup Error"

        def build(self):
            root = BoxLayout(
                orientation="vertical",
                padding=dp(12),
                spacing=dp(10),
            )

            title = Label(
                text="خطای شروع برنامه رخ داد",
                size_hint_y=None,
                height=dp(48),
                font_size="18sp",
            )
            root.add_widget(title)

            scroll = ScrollView()
            label = Label(
                text=report,
                size_hint_y=None,
                halign="left",
                valign="top",
                font_size="12sp",
            )
            label.bind(
                width=lambda instance, value: setattr(
                    instance, "text_size", (value, None)
                )
            )
            label.bind(
                texture_size=lambda instance, value: setattr(
                    instance, "height", value[1] + dp(20)
                )
            )
            scroll.add_widget(label)
            root.add_widget(scroll)

            copy_button = Button(
                text="Copy error",
                size_hint_y=None,
                height=dp(48),
            )
            copy_button.bind(on_release=lambda *_: Clipboard.copy(report))
            root.add_widget(copy_button)
            return root

        def on_start(self):
            try:
                from pathlib import Path
                report_path = Path(self.user_data_dir) / "javanrood_crash_report.txt"
                report_path.write_text(report, encoding="utf-8")
            except Exception:
                pass

    CrashReportApp().run()


def main() -> int:
    try:
        from javanrood_app import main as run_application
        return int(run_application() or 0)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else 0
    except BaseException:
        report = traceback.format_exc()
        print("\n===== JAVANROOD STARTUP CRASH =====", file=sys.stderr)
        print(report, file=sys.stderr, flush=True)

        try:
            _run_diagnostic_screen(report)
        except BaseException:
            print(
                traceback.format_exc(),
                file=sys.stderr,
                flush=True,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
