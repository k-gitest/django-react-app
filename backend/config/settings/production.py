from .base import *

DEBUG = False

# Render等の環境変数から取得
# ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=lambda v: [s.strip() for s in v.split(",") if s.strip()])

# 本番データベース設定 (SSL必須)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("PGDATABASE"),
        "USER": config("PGUSER"),
        "PASSWORD": config("PGPASSWORD"),
        "HOST": config("PGHOST"),
        "PORT": config("PGPORT", default=5432, cast=int),
        "OPTIONS": {
            "sslmode": "require",
        },
        "DISABLE_SERVER_SIDE_CURSORS": True,
    }
}

# 本番用ストレージ (Backblaze B2 / S3)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
    },
}

# セキュリティ設定
CSRF_COOKIE_SECURE = True
JWT_AUTH_SECURE = True

# allauthの本番設定
ACCOUNT_EMAIL_VERIFICATION = "mandatory"