from .base import *

DEBUG = True

# ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# データベース設定 (SSLなし)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("PGDATABASE", default=""),
        "USER": config("PGUSER", default=""),
        "PASSWORD": config("PGPASSWORD", default=""),
        "HOST": config("PGHOST", default="localhost"),
        "PORT": config("PGPORT", default=5432, cast=int),
    }
}

# 開発用ストレージ (ローカルファイル)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ローカルではCookieのセキュリティを緩和（http接続のため）
CSRF_COOKIE_SECURE = False
JWT_AUTH_SECURE = False