from .settings import *
import os

# Database
# **********************************************
# テスト用：SQLite（インメモリ）
# **********************************************

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# テスト高速化
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # 高速だが安全ではない（テスト用）
]

# その他のテスト用設定
DEBUG = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ストレージ設定（テスト時は不要）
AWS_STORAGE_BUCKET_NAME = None

# 環境変数（ダミー）
QSTASH_TOKEN = 'test_token'
QSTASH_CURRENT_SIGNING_KEY = 'test_key'
QSTASH_NEXT_SIGNING_KEY = 'test_key'
RESEND_API_KEY = 'test_api_key'
WEBHOOK_BASE_URL = 'http://localhost:8000'
FRONT_URL = 'http://localhost:3000'

# キャッシュ（テスト用）
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# テスト環境フラグ
TESTING = True