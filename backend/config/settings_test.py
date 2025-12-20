from .settings import *

# Database
# **********************************************
# テスト用：インメモリSQLite設定
# **********************************************

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # 'NAME': ':memory:' を使用すると、テスト終了時にデータベースファイルが残りません
        # 注意: ':memory:' はファイルシステム上ではなくメモリ上に作成されます
        "NAME": ":memory:", 
    }
}

# テスト高速化
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # 高速だが安全ではない（テスト用）
]

# その他のテスト用設定
DEBUG = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'