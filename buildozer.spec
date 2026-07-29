[app]
# توجه: «title» عمداً انگلیسی نگه داشته شده است. buildozer/
# python-for-android در پردازش عنوان‌های غیر-ASCII (مثل فارسی) داخل
# فایل‌های تولیدی گریدل (strings.xml، AndroidManifest) با
# UnicodeDecodeError یا شکست بی‌صدا در فاز packaging مواجه می‌شوند و
# نتیجه‌اش دقیقاً همین حالت است: بیلد ظاهراً تا انتها می‌رود اما هیچ
# APK ای در bin/ ساخته نمی‌شود. نام نمایشی فارسی در فاز بعدی، با یک
# روش امن (ویرایش مستقیم strings.xml تولیدشده توسط p4a، نه یک فایل
# res موازی که با آن تصادم می‌کند) اضافه خواهد شد.
title = Javanrood Committee Client
package.name = javanroodcommitteeclient
package.domain = ir.javanrood

source.dir = src
source.include_exts = py,kv,png,jpg,ttf,otf,json
source.include_patterns = ../assets/*,../assets/fonts/*

version = 1.0.0

requirements = python3==3.12.8,hostpython3==3.12.8,cryptography==46.0.3,kivy==2.3.1,arabic_reshaper,python-bidi,pyjnius

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/../assets/javanrood_app.png

# آیکون آداپتیو کامل (legacy mipmap + round + foreground/background برای
# اندروید ۸+) که با اسکریپت طراحی آیکون در assets/android_res تولید شده؛
# این پوشه مستقیماً به res/ پروژه گریدل اضافه می‌شود.
android.add_resources = %(source.dir)s/../assets/android_res

android.permissions = INTERNET
android.api = 34
android.minapi = 26
android.ndk = 28c
# فقط arm64-v8a برای فاز اول: هدف این مرحله رسیدن به یک APK سالم و
# قابل نصب است، نه پوشش کامل معماری‌ها. armeabi-v7a (۳۲بیتی) بعداً که
# زیرساخت build پایدار شد اضافه می‌شود؛ برخی recipeهای native (مثل
# libffi) گاهی روی این arch با NDKهای جدید مشکل build دارند و اضافه
# کردنش همین الان فقط سطح خطای قابل‌بررسی را بالا می‌برد.
android.archs = arm64-v8a
android.allow_backup = False

# داده‌های مجوز و رکوردها باید در فضای داخلی/خصوصی برنامه بمانند، نه
# روی حافظه اشتراکی خارجی، برای حفظ مدل امنیتی مجوز.
android.private_storage = True

[buildozer]
log_level = 2
warn_on_root = 1
