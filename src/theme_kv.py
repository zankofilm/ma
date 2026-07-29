# -*- coding: utf-8 -*-
"""پالت رنگ رسمی سرمه‌ای/طلایی، معادل نسخه دسکتاپ، برای استفاده در Kivy."""

COLOR_NAVY_DARK = "0b1f3a"
COLOR_NAVY = "13294b"
COLOR_NAVY_LIGHT = "1f3a63"
COLOR_GOLD = "c9a227"
COLOR_GOLD_LIGHT = "e0c34f"
COLOR_BG = "f4f5f7"
COLOR_CARD_BG = "ffffff"
COLOR_TEXT_DARK = "1c2530"
COLOR_TEXT_MUTED = "5b6472"
COLOR_BORDER = "d7dbe3"
COLOR_DANGER = "a4262c"
COLOR_SUCCESS = "256029"


def hex_to_rgba(hex_color: str, alpha: float = 1.0):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, alpha)


RGBA_NAVY_DARK = hex_to_rgba(COLOR_NAVY_DARK)
RGBA_NAVY = hex_to_rgba(COLOR_NAVY)
RGBA_GOLD = hex_to_rgba(COLOR_GOLD)
RGBA_BG = hex_to_rgba(COLOR_BG)
RGBA_CARD_BG = hex_to_rgba(COLOR_CARD_BG)
RGBA_TEXT_DARK = hex_to_rgba(COLOR_TEXT_DARK)
RGBA_TEXT_MUTED = hex_to_rgba(COLOR_TEXT_MUTED)
RGBA_BORDER = hex_to_rgba(COLOR_BORDER)
RGBA_DANGER = hex_to_rgba(COLOR_DANGER)
RGBA_SUCCESS = hex_to_rgba(COLOR_SUCCESS)
