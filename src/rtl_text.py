# -*- coding: utf-8 -*-
"""نمایش صحیح متن فارسی/عربی در Kivy.

Kivy به‌خودی‌خود شکل‌دهی حروف چسبان (glyph shaping) فارسی و عربی و
ترتیب راست‌به‌چپ را انجام نمی‌دهد؛ رشته‌های حاوی حروف فارسی باید قبل
از قرارگیری در هر ویجت متنی (Label، Button، TextInput و...) از این
تابع عبور کنند تا صورت درست و به‌ترتیب صحیح روی صفحه نمایش داده شوند.

نکته: TextInput ورودی کاربر (تایپ) را خام نگه می‌داریم و فقط هنگام
نمایش reshape می‌کنیم، وگرنه ویرایش متن (backspace/cursor) خراب می‌شود.
"""
from __future__ import annotations

import re

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _RESHAPE_AVAILABLE = True
except Exception:
    _RESHAPE_AVAILABLE = False

_PERSIAN_RANGE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]"
)

_reshaper_config = None


def _get_reshaper():
    global _reshaper_config
    if _reshaper_config is None and _RESHAPE_AVAILABLE:
        _reshaper_config = arabic_reshaper.ArabicReshaper(
            {
                "delete_harakat": True,
                "support_ligatures": True,
                "language": "Farsi",
            }
        )
    return _reshaper_config


def has_persian(text: str) -> bool:
    return bool(text) and bool(_PERSIAN_RANGE.search(text))


def fa(text) -> str:
    """رشته را برای نمایش صحیح در ویجت‌های Kivy آماده می‌کند.

    خطوط را جدا-جدا پردازش می‌کند تا چیدمان چندخطی (متن چندسطری در
    QLabel/TextInput) به‌هم نریزد؛ رشته غیر-فارسی یا خالی بدون تغییر
    برمی‌گردد.
    """
    if text is None:
        return ""
    text = str(text)
    if not _RESHAPE_AVAILABLE or not has_persian(text):
        return text
    reshaper = _get_reshaper()
    lines = text.split("\n")
    out_lines = []
    for line in lines:
        if has_persian(line):
            reshaped = reshaper.reshape(line) if reshaper else line
            out_lines.append(get_display(reshaped))
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


__all__ = ["fa", "has_persian"]
