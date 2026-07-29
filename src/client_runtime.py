# -*- coding: utf-8 -*-
"""مسیرهای اجرا و ذخیره‌سازی، مخصوص اندروید.

روی اندروید، داده‌های برنامه باید در مسیر داخلی و خصوصی اپ ذخیره شوند
(app-private storage) که با نصب حذف برنامه پاک می‌شود ولی برای سایر
برنامه‌ها یا کاربر به‌صورت مستقیم قابل دسترسی نیست؛ این دقیقاً معادل
همان مسیر AppData ویندوز در نسخه دسکتاپ است.
"""
from __future__ import annotations

import os
from pathlib import Path

APP_FOLDER = "JavanroodCommitteeClient"


def base_dir() -> Path:
    """مسیر پایه دارایی‌های برنامه (assets) که در APK بسته‌بندی شده‌اند."""
    try:
        from android.storage import app_storage_path  # type: ignore
        return Path(app_storage_path())
    except Exception:
        return Path(__file__).resolve().parent


def data_dir() -> Path:
    """مسیر خصوصی و پایدار برای ذخیره داده‌های رمزنگاری‌شده کلاینت."""
    try:
        from android.storage import app_storage_path  # type: ignore
        path = Path(app_storage_path()) / APP_FOLDER
    except Exception:
        # اجرای خارج از اندروید (مثلاً برای تست‌های خودکار روی دسکتاپ/CI)
        if os.name == "nt":
            root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        else:
            root = str(Path.home() / ".local" / "share")
        path = Path(root) / APP_FOLDER
    path.mkdir(parents=True, exist_ok=True)
    return path


def asset_path(*parts: str) -> str:
    return str(base_dir().joinpath("assets", *parts))
