import newrelic.agent
import logging
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from datetime import timedelta
from pathlib import Path
from decouple import config
from apps.common.error_reporting import _before_send
from corsheaders.defaults import default_headers


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = config("SECRET_KEY")

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
    'drf_spectacular',
    "strawberry_django",
    "apps.common",
    "apps.users",
    "apps.todos",
    'apps.webhooks',
    "apps.analytics",
    "apps.data_pipeline",
    'apps.graphql_api',
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

LANGUAGE_CODE = "ja"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

# collectstaticの集約先ディレクトリを定義
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ALLOWED_HOSTS = []

# フロントエンドURL
FRONTEND_URL = config("FRONT_URL", default="http://localhost:3000")

# 開発環境で、特定のオリジンからのアクセスを許可
# React の開発サーバーが動いているポート 3000 を許可します
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",  # 127.0.0.1 も念のため追加しておくのが安全
    FRONTEND_URL,
]

# 本番環境では False に設定し、CORS_ALLOWED_ORIGINS または CORS_ALLOWED_HOSTS を厳密に定義すべき
CORS_ALLOW_CREDENTIALS = True  # クッキーや認証ヘッダーを含める場合に必要

# 許可するヘッダー
CORS_ALLOW_HEADERS = list(default_headers) + [
    # Sentry
    "sentry-trace",
    "baggage",
    
    # New Relic
    "traceparent",
    "tracestate",
    "newrelic",
]

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
    "EXCEPTION_HANDLER": "apps.common.error_handlers.custom_exception_handler",
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
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
    #"REGISTER_SERIALIZER": "dj_rest_auth.registration.serializers.RegisterSerializer",
    "TOKEN_MODEL": None,
    # カスタムシリアライザ
    "USER_DETAILS_SERIALIZER": "apps.users.serializers.CustomUserSerializer",  # ユーザー情報取得用
    "REGISTER_SERIALIZER": "apps.users.serializers.CustomRegisterSerializer",  # ユーザー登録用
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
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default=None)  # Backblaze Key ID
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default=None)  # Backblaze Key
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default=None)
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default=None)  # Backblaze エンドポイント
AWS_S3_REGION_NAME = "us-west-004"  # Backblaze リージョン

# S3互換設定
AWS_S3_CUSTOM_DOMAIN = None  # CDNを使わない場合
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",  # 1日キャッシュ
}

# ストレージバックエンド設定
"""
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
"""

# メディアファイルのURL設定
if AWS_S3_ENDPOINT_URL:
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
else:
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# キャッシュ設定
REDIS_URL = config("REDIS_URL", default="redis://127.0.0.1:6379/1")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
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

# qstash設定
QSTASH_TOKEN = config("QSTASH_TOKEN", default=None)
QSTASH_CURRENT_SIGNING_KEY = config("QSTASH_CURRENT_SIGNING_KEY", default=None)
QSTASH_NEXT_SIGNING_KEY = config("QSTASH_NEXT_SIGNING_KEY", default=None)

# resend設定
RESEND_API_KEY = config("RESEND_API_KEY", default=None)
WEBHOOK_BASE_URL = config("WEBHOOK_BASE_URL", "http://localhost:8000")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", "noreply@example.com")

# Vector Search & Embeddings
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default="")
UPSTASH_VECTOR_REST_URL = config("UPSTASH_VECTOR_REST_URL", default="")
UPSTASH_VECTOR_REST_TOKEN = config("UPSTASH_VECTOR_REST_TOKEN", default="")

# ===== MotherDuck =====
MOTHERDUCK_TOKEN = config("MOTHERDUCK_TOKEN", default="")

DEBUG = False

# Sentry設定
if not DEBUG or config('SENTRY_ENABLED', default=False, cast=bool):
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(
                level=logging.INFO,        # ログレベル INFO以上をSentryに送信
                event_level=logging.ERROR  # ERROR以上はイベントとして記録
            ),
        ],
        
        # パフォーマンス監視
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
        
        # プロファイリング
        profiles_sample_rate=config('SENTRY_PROFILES_SAMPLE_RATE', default=0.1, cast=float),
        
        # 環境設定
        environment=config('ENVIRONMENT', default='development'),
        
        # リリース情報（Git commit hashなど）
        release=config('RELEASE', default='unknown'),
        
        # エラーサンプリング（本番環境で全エラーを送信すると課金が大きくなる）
        sample_rate=1.0,  # 100%のエラーを送信（小規模なら問題ない）
        
        # 機密情報のフィルタリング
        send_default_pii=False,  # 個人情報を送信しない
        
        # パフォーマンス
        max_breadcrumbs=50,
        
        # エラーの前処理
        before_send=_before_send,
    )

# New Relic初期化（本番環境のみ）
NEW_RELIC_LICENSE_KEY = config('NEW_RELIC_LICENSE_KEY', default='')
NEW_RELIC_APP_NAME = config('NEW_RELIC_APP_NAME', default='django-react-app-backend')
NEW_RELIC_ENVIRONMENT = config('NEW_RELIC_ENVIRONMENT', default='development')

# 本番環境のみNew Relicを初期化
if not DEBUG and config('NEW_RELIC_LICENSE_KEY', default=''):
    newrelic.agent.initialize()

# open api schema設定
SPECTACULAR_SETTINGS = {
    'TITLE': 'Django React App API',
    'DESCRIPTION': 'Django/React モノレポベースのSPAアプリケーション',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    
    # 認証設定
    'SECURITY': [
        {
            'cookieAuth': [],  # JWT Cookie認証
        }
    ],
    'SECURITY_DEFINITIONS': {
        'cookieAuth': {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'access-token',
        }
    },
    
    # レスポンス設定
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
}