from datetime import timedelta
from os import getenv
from pathlib import Path

from decouple import config
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = "django-insecure-h6r^b$7t39=-1p%q_6vxnsq2zzbb#qa5wf*5cu7&uskbs#)_-="
SECRET_KEY = config("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "storages",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "users",
    "todos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("PGDATABASE"),
        "USER": getenv("PGUSER"),
        "PASSWORD": getenv("PGPASSWORD"),
        "HOST": getenv("PGHOST"),
        "PORT": getenv("PGPORT", 5432),
        "OPTIONS": {
            "sslmode": "require",
        },
        "DISABLE_SERVER_SIDE_CURSORS": True,
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# collectstaticの集約先ディレクトリを定義
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 開発環境で、特定のオリジンからのアクセスを許可
# React の開発サーバーが動いているポート 3000 を許可します
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",  # 127.0.0.1 も念のため追加しておくのが安全
    getenv("FRONT_URL"),
]

# 本番環境では False に設定し、CORS_ALLOWED_ORIGINS または CORS_ALLOWED_HOSTS を厳密に定義すべき
CORS_ALLOW_CREDENTIALS = True  # クッキーや認証ヘッダーを含める場合に必要

# CSRFトークンもCookieで送る
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_HTTPONLY = False  # フロントエンドから読み取り可能にする
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# REST FrameWorkの設定
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        # 'rest_framework.permissions.IsAuthenticated',
        "rest_framework.permissions.AllowAny",
    ),
    "EXCEPTION_HANDLER": "users.exceptions.custom_exception_handler",
}

# dj-rest-authの設定
REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": "access-token",
    "JWT_AUTH_REFRESH_COOKIE": "refresh-token",
    "SESSION_LOGIN": False,
    "JWT_AUTH_HTTPONLY": True,  # XSS対策
    "JWT_AUTH_SAMESITE": "None",
    "JWT_AUTH_SECURE": True,
    "SESSION_LOGIN": False,
    "REGISTER_SERIALIZER": "dj_rest_auth.registration.serializers.RegisterSerializer",
    "TOKEN_MODEL": None,
    # カスタムシリアライザ
    "USER_DETAILS_SERIALIZER": "users.serializers.CustomUserSerializer",  # ユーザー情報取得用
    "REGISTER_SERIALIZER": "users.serializers.CustomRegisterSerializer",  # ユーザー登録用
}

# Simple JWT の設定
SIMPLE_JWT = {
    # 👈 アクセストークンは短命に設定するのが一般的
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    # 👈 リフレッシュトークンは長めに設定し、再ログイン頻度を減らす
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    # "ALGORITHM": "HS256",  # 👈 デフォルトの対称鍵署名
    # "SIGNING_KEY": "YOUR_SUPER_SECRET_KEY", # 👈 settings.SECRET_KEY がデフォルトで使われる
    "BLACKLIST_AFTER_ROTATION": True,
    # ヘッダーはデフォルトでJWTなのでBearerを設定
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# カスタムユーザーモデルのフルパスを設定
AUTH_USER_MODEL = "users.CustomUser"

# allauth
SITE_ID = 1
# 認証方式の設定
ACCOUNT_AUTHENTICATION_METHOD = "email"  # emailで認証
ACCOUNT_EMAIL_REQUIRED = True  # email必須
ACCOUNT_USERNAME_REQUIRED = False  # username不要
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # usernameフィールドを使わない
ACCOUNT_EMAIL_VERIFICATION = "none"  # 開発環境では無効化（本番では'mandatory'推奨）
# カスタムユーザーモデルのフィールド設定
# これがないとallauthがusernameフィールドを探してエラーになる
USER_MODEL_USERNAME_FIELD = None

# AWS S3 / Backblaze B2設定
# django-storagesが以下の環境変数を自動的に読み込む
AWS_ACCESS_KEY_ID = getenv("AWS_ACCESS_KEY_ID")  # Backblaze Key ID
AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")  # Backblaze Key
AWS_STORAGE_BUCKET_NAME = getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = getenv("AWS_S3_ENDPOINT_URL")  # Backblaze エンドポイント
AWS_S3_REGION_NAME = "us-west-004"  # Backblaze リージョン

# S3互換設定
AWS_S3_CUSTOM_DOMAIN = None  # CDNを使わない場合
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",  # 1日キャッシュ
}

# ストレージバックエンド設定
if AWS_STORAGE_BUCKET_NAME:
    # 本番環境：Backblaze B2を使用
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
        },
    }
else:
    # 開発環境：ローカルファイルシステムを使用
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# メディアファイルのURL設定
if AWS_S3_ENDPOINT_URL:
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
else:
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# キャッシュ設定
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": getenv("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # UpstashはSSL必須。証明書検証でエラーが出る場合は以下を指定
            "CONNECTION_POOL_KWARGS": {
                "ssl_cert_reqs": None,
            },
        },
    }
}

# セッション設定
# セッションの保存先をキャッシュ（Redis）に指定
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# 使用するキャッシュの名前（CACHESで定義した 'default' を使用）
SESSION_CACHE_ALIAS = "default"

# セッションの有効期限設定（必要に応じて調整）
SESSION_COOKIE_AGE = 1209600  # 2週間（秒単位）
SESSION_SAVE_EVERY_REQUEST = (
    False  # リクエストごとに保存するとRedisへの負荷が増えるため通常はFalse
)
