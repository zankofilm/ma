[app]
title = کلاینت کمیته‌های محلات جوانرود
package.name = javanroodcommitteeclient
package.domain = ir.javanrood

source.dir = src
source.include_exts = py,kv,png,jpg,ttf,otf,json
source.include_patterns = ../assets/*,../assets/fonts/*

version = 1.0.0

requirements = python3,kivy==2.3.1,cryptography==42.0.8,argon2-cffi,arabic_reshaper,python-bidi,pyjnius

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/../assets/javanrood_app.png

# آیکون آداپتیو کامل (legacy mipmap + round + foreground/background برای
# اندروید ۸+) که با اسکریپت طراحی آیکون در assets/android_res تولید شده؛
# این پوشه مستقیماً به res/ پروژه گریدل اضافه می‌شود.
android.add_resources = %(source.dir)s/../assets/android_res

android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False

# داده‌های مجوز و رکوردها باید در فضای داخلی/خصوصی برنامه بمانند، نه
# روی حافظه اشتراکی خارجی، برای حفظ مدل امنیتی مجوز.
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
