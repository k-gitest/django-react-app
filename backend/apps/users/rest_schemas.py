from drf_spectacular.utils import extend_schema, OpenApiExample
from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers
from .serializers import CustomRegisterSerializer, AuthResponseSerializer, WelcomeEmailWebhookSerializer

def get_register_schema():
    """
    登録APIのスキーマ定義を返す
    
    関数にすることで、インポート時ではなく使用時に評価される
    """
    
    return extend_schema(
        summary="新規登録",
        description="""
        新規ユーザーを登録します。
        
        **機能:**
        - HttpOnly CookieにJWTトークンを自動設定
        - ウェルカムメールを非同期送信（QStash経由）
        - 登録イベントを記録（MotherDuck Analytics）
        
        **レート制限:** 3回/1時間
        
        **成功時の動作:**
        1. ユーザー作成
        2. アクセストークン（5分間有効）をCookieに設定
        3. リフレッシュトークン（1日間有効）をCookieに設定
        4. ウェルカムメールを非同期で送信（失敗してもユーザー作成は成功）
        5. 登録イベントをMotherDuckに記録（失敗してもユーザー作成は成功）
        """,
        request=CustomRegisterSerializer,
        responses={
            201: AuthResponseSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                    'data': {'type': 'object'},
                }
            },
            429: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                }
            },
        },
        examples=[
            OpenApiExample(
                'Success',
                value={
                    'user': {
                        'id': 1,
                        'email': 'user@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'is_staff': False
                    },
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                },
                response_only=True,
                status_codes=['201'],
            ),
            OpenApiExample(
                'User Already Exists',
                value={
                    'error': 'user_already_exists',
                    'detail': 'メールアドレス user@example.com は既に登録されています',
                    'data': {'field': 'email'}
                },
                response_only=True,
                status_codes=['400'],
            ),
            OpenApiExample(
                'Too Many Requests',
                value={
                    'detail': 'リクエストが多すぎます。'
                },
                response_only=True,
                status_codes=['429'],
            ),
        ],
        tags=['Authentication']
    )

def get_login_schema():
    """ログインAPIのスキーマ定義を返す"""
    
    return extend_schema(
        summary="ログイン",
        description="""
        メールアドレスとパスワードでログインします。
        
        **機能:**
        - HttpOnly CookieにJWTトークンを設定
        - ログイン履歴を記録（MotherDuck Analytics）
        
        **レート制限:** 5回/5分
        
        **成功時の動作:**
        1. アクセストークン（5分間有効）をCookieに設定
        2. リフレッシュトークン（1日間有効）をCookieに設定
        3. ログインイベントをMotherDuckに記録
        """,
        request=LoginSerializer,
        responses={
            200: AuthResponseSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'non_field_errors': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            },
            429: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                }
            },
        },
        examples=[
            OpenApiExample(
                'Success',
                value={
                    'user': {
                        'id': 1,
                        'email': 'user@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'is_staff': False
                    },
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                'Bad Request - Invalid Credentials',
                value={
                    'non_field_errors': ['メールアドレスまたはパスワードが正しくありません。']
                },
                response_only=True,
                status_codes=['400'],
            ),
            OpenApiExample(
                'Too Many Requests',
                value={
                    'detail': 'リクエストが多すぎます。しばらく時間を置いてから再度お試しください。'
                },
                response_only=True,
                status_codes=['429'],
            ),
        ],
        tags=['Authentication']
    )


def get_logout_schema():
    """ログアウトAPIのスキーマ定義を返す"""
    return extend_schema(
        summary="ログアウト",
        description="""
        現在のセッションからログアウトします。
        
        **機能:**
        - リフレッシュトークンをブラックリストに追加
        - Cookieをクリア
        - ログアウトイベントを記録（MotherDuck Analytics）
        
        **注意:** ログアウト後は、再度ログインが必要です。
        """,
        request=serializers.Serializer,  # 空のリクエスト
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'detail': {
                        'type': 'string',
                        'example': 'ログアウトしました。'
                    }
                }
            },
        },
        tags=['Authentication']
    )

def user_webhook_send_welcome_email_schema():
    """Webhook用スキーマ（内部API）"""
    
    return extend_schema(
        summary="[内部API] ウェルカムメール送信",
        description="""
        QStashから呼ばれる内部エンドポイント。直接呼び出し不可。
        
        **セキュリティ:**
        - QStash署名検証（HMAC-SHA256）
        - IPアドレス制限なし（署名のみで認証）
        
        **リトライ:**
        - QStashが自動リトライ（最大3回）
        - 5秒、10秒、15秒の間隔
        
        **エラー時の動作:**
        - 500エラー: QStashが自動リトライ
        - 400エラー: リトライなし（データ不正）
        """,
        request=WelcomeEmailWebhookSerializer,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'message_id': {'type': 'string'},
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'email': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    },
                    'first_name': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    },
                }
            },
            401: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        examples=[
            OpenApiExample(
                'Success',
                value={
                    'message': 'Email sent successfully',
                    'message_id': 're_abc123xyz'
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                'Bad Request',
                value={
                    'email': ['この項目は必須です。'],
                    'first_name': ['この項目は必須です。']
                },
                response_only=True,
                status_codes=['400'],
            ),
            OpenApiExample(
                'Unauthorized',
                value={'detail': 'QStash署名検証に失敗しました。'},
                response_only=True,
                status_codes=['401'],
            ),
            OpenApiExample(
                'Internal Server Error',
                value={
                    'error': 'email_delivery_error',
                    'detail': 'メール送信に失敗しました。'
                },
                response_only=True,
                status_codes=['500'],
            ),
        ],
        tags=['Internal', 'Webhooks'],
        # ドキュメントから除外する場合は以下を追加
        # exclude=True
    )