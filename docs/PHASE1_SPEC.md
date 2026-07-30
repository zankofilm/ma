# فاز ۱ — فعال‌سازی Native Android

## دامنه این فاز

این نسخه فقط شامل فعال‌سازی و تمدید است:

1. ساخت کلید Ed25519 اختصاصی نصب برنامه
2. نگهداری seed کلید با AES-GCM در Android Keystore
3. ساخت شناسه پایدار نصب و هش ۶۴ رقمی
4. ساخت فایل `.jrr` سازگار با ادمین Python
5. انتخاب فایل `.jra` با فایل‌انتخاب‌کن داخلی Android
6. اعتبارسنجی امضای Ed25519 مدیر
7. مشتق‌سازی Scrypt با پارامترهای نسخه ادمین
8. رمزگشایی AES-256-GCM
9. کنترل کد ملی، دستگاه و کلید درخواست
10. ذخیره رمزنگاری‌شده مجوز و نمایش مشخصات

## سازگاری پروتکل

- Request format: `JAVANROOD-CLIENT-REQUEST`
- Activation format: `JAVANROOD-CLIENT-ACTIVATION`
- Protocol version: `1`
- Request signature: Ed25519
- Activation signature: Ed25519
- Activation KDF: Scrypt `N=32768, r=8, p=1, length=32`
- Activation encryption: AES-256-GCM
- Base64: URL-safe همراه padding
- Canonical JSON: کلیدهای مرتب، بدون فاصله، UTF-8 بدون ASCII escaping

## وابستگی به برنامه جانبی

برنامه پس از نصب برای اجرا به Chrome، WebView، Python، Kivy، Buildozer،
Termux یا ADB نیاز ندارد. فایل‌ها از طریق Storage Access Framework خود
Android انتخاب و ذخیره می‌شوند.
