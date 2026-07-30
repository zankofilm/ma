[app]
title = Javanrood Client Clean
package.name = javanroodcommitteeclientclean
package.domain = ir.javanrood

source.dir = src
source.include_exts = py,kv,png,jpg,ttf,otf,json

version = 1.2.0
requirements = python3==3.12.8,hostpython3==3.12.8,kivy==2.3.1,android,pyjnius,filetype,cryptography==46.0.3,arabic_reshaper,python-bidi

orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/../assets/javanrood_app.png

android.permissions = INTERNET
android.api = 34
android.minapi = 26
android.ndk_api = 26
android.ndk = 28c
android.archs = arm64-v8a
android.allow_backup = False
android.private_storage = True
android.logcat_filters = *:S python:V SDL:V AndroidRuntime:E libc:E

p4a.bootstrap = sdl2
p4a.branch = v2026.05.09
p4a.commit = 58d2114

[buildozer]
log_level = 2
warn_on_root = 1
