from .settings import *
import os

# Database
# **********************************************
# テスト用：PostgreSQL設定
# **********************************************

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('PGDATABASE', 'test_db'),
        'USER': os.getenv('PGUSER', 'postgres'),
        'PASSWORD': os.getenv('PGPASSWORD', 'postgres'),
        'HOST': os.getenv('PGHOST', 'localhost'),
        'PORT': os.getenv('PGPORT', '5432'),
        'OPTIONS': {
            # テスト環境（Docker内など）ではSSLをオフ
            'sslmode': 'disable',
        },
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