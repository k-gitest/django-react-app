from .base import *

# テスト環境フラグ
TESTING = True
DEBUG = False

# Database: 高速化のためSQLite（インメモリ）を使用
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# キャッシュ: Redisを使わずメモリ上で完結させる（テストの独立性確保）
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# パスワードハッシュの高速化
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# メールの実送信を無効化
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ストレージ設定（テスト時はローカル扱いにし、外部接続を避ける）
AWS_STORAGE_BUCKET_NAME = None
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# 外部サービス用ダミー環境変数
QSTASH_TOKEN = 'test_token'
QSTASH_CURRENT_SIGNING_KEY = 'test_key'
QSTASH_NEXT_SIGNING_KEY = 'test_key'
RESEND_API_KEY = 'test_api_key'
WEBHOOK_BASE_URL = 'http://localhost:8000'
FRONTEND_URL = 'http://localhost:3000'  # base.pyの変数名に合わせる