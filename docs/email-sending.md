# メール送信機能詳細ガイド

## 目次

- [概要](#概要)
- [アーキテクチャ](#アーキテクチャ)
- [実装構成](#実装構成)
- [QStash Service実装](#qstash-service実装)
- [Resend設定](#resend設定)
- [Webhook実装](#webhook実装)
- [セキュリティ](#セキュリティ)
- [環境変数設定](#環境変数設定)
- [開発環境での確認](#開発環境での確認)
- [トラブルシューティング](#トラブルシューティング)
- [ベストプラクティス](#ベストプラクティス)

---

## 概要

ユーザー登録時に**QStash + Resend**を使用してウェルカムメールを非同期送信します。

**主な機能**:
- ⚡ ユーザー登録が高速（メール送信を待たない）
- 🔄 自動リトライ（QStashが最大3回再送）
- 🐳 Renderのスリープ対応
- 🧪 テストフレンドリー

---

## アーキテクチャ

### フロー全体

```
ユーザー登録リクエスト
    ↓
Django View（CustomRegisterView）
    ↓
UserRegistrationService.register_user()
    ├─ ユーザー作成（同期、50ms）
    └─ transaction.on_commit() でメール送信を予約
        ↓
UserQStashService.send_welcome_email_async()
    ├─ QStashにメッセージ送信（非同期、1ms）
    └─ 即座にレスポンス返却 ⚡
        ↓
--- バックグラウンド処理 ---
        ↓
QStash（1秒後に配信）
    ↓
Webhook: /api/v1/webhooks/send-welcome-email
    ↓
UserEmailService.send_welcome_email()
    ↓
Resend API
    ↓
ユーザーにメール送信
```

### なぜ非同期か？

**同期処理の問題点**:
```python
# ❌ 同期処理（変更前）
def register_user(user_data):
    user = create_user(...)
    send_email(user.email)  # ← ここで200-300ms待つ
    return user

# レスポンス時間: 250-350ms
```

**非同期処理のメリット**:
```python
# ✅ 非同期処理（変更後）
def register_user(user_data):
    user = create_user(...)
    queue_email(user.email)  # ← 1ms
    return user

# レスポンス時間: 50-100ms（3-5倍高速）
```

---

## 実装構成

```
backend/
├── users/
│   ├── services/
│   │   ├── registration_service.py  # ユーザー登録
│   │   ├── email_service.py         # メール送信（Resend）
│   │   └── qstash_service.py        # QStash連携
│   │
│   └── views.py                     # CustomRegisterView
│
├── webhooks/
│   ├── views.py                     # Webhookエンドポイント
│   └── urls.py                      # Webhook統合ルーティング
│
└── common/
    ├── infrastructure/
    │   └── qstash_client.py         # QStashClient（汎用）
    │
    └── permissions.py               # IsQStashAuthenticated
```

---

## QStash Service実装

### BaseQStashService（共通基盤）

```python
# backend/common/infrastructure/base_qstash_service.py
class BaseQStashService:
    """
    QStash共通機能
    
    Users（メール送信）とTodos（ベクトル化）で共通利用
    """
    
    @classmethod
    def _safe_publish(
        cls, 
        endpoint_path: str, 
        payload: dict, 
        delay_seconds: int = 0
    ) -> str:
        """
        QStashにメッセージを安全に送信
        
        例外を QStashError に変換
        """
        try:
            message_id = QStashClient.publish(endpoint_path, payload, delay_seconds)
            
            if not message_id or not isinstance(message_id, str):
                raise QStashError(
                    message="Invalid response from QStash client",
                    endpoint=endpoint_path
                )
            
            return message_id
            
        except QStashError:
            raise
        except Exception as e:
            raise QStashError(
                message=f"QStash operation failed: {str(e)}",
                endpoint=endpoint_path
            ) from e
```

### UserQStashService（ユーザー向け）

```python
# backend/users/services/qstash_service.py
class UserQStashService(BaseQStashService):
    """
    ユーザー関連のQStash操作
    
    ウェルカムメール送信など
    """
    
    ENDPOINT_WELCOME_EMAIL: Final = "/api/v1/webhooks/send-welcome-email"
    
    @classmethod
    @service_error_handler
    def send_welcome_email_async(cls, email: str, first_name: str) -> str:
        """
        ウェルカムメール送信をキューに追加
        
        Args:
            email: 送信先メールアドレス
            first_name: ユーザーの名前
        
        Returns:
            QStash message ID
        """
        payload = {
            "email": email,
            "first_name": first_name
        }
        
        return cls._safe_publish(cls.ENDPOINT_WELCOME_EMAIL, payload)
```

### QStashClient（Infrastructure層）

```python
# backend/common/infrastructure/qstash_client.py
import requests

class QStashClient:
    """
    QStashを使った非同期タスク送信（汎用版）
    """
    
    BASE_URL = "https://qstash.upstash.io/v2"
    
    @staticmethod
    def publish(endpoint_path: str, payload: dict, delay_seconds: int = 0) -> str:
        """
        QStashにメッセージを送信
        
        Args:
            endpoint_path: Webhookエンドポイント（例: /api/v1/webhooks/send-welcome-email）
            payload: 送信するJSON
            delay_seconds: 遅延秒数（デフォルト: 0）
        
        Returns:
            QStash message ID
        """
        webhook_url = f"{settings.WEBHOOK_BASE_URL}{endpoint_path}"
        
        headers = {
            "Authorization": f"Bearer {settings.QSTASH_TOKEN}",
            "Content-Type": "application/json",
        }
        
        if delay_seconds > 0:
            headers["Upstash-Delay"] = f"{delay_seconds}s"
        
        response = requests.post(
            f"{QStashClient.BASE_URL}/publish/{webhook_url}",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        response.raise_for_status()
        return response.json()["messageId"]
```

---

## Resend設定

### Resendとは？

**Resend** は開発者フレンドリーなメール送信サービスです。

**特徴**:
- ✅ シンプルなAPI
- ✅ 高い到達率
- ✅ 無料枠: 3,000通/月、100通/日
- ✅ React Email統合

### アカウント作成

```
1. https://resend.com/ にアクセス
2. Sign Up（GitHubアカウントでOK）
3. API Keys → Create API Key
4. ドメイン認証（オプション、到達率向上）
```

### UserEmailService実装

```python
# backend/users/services/email_service.py
import resend

class UserEmailService:
    """
    ユーザー向けメール送信サービス
    """
    
    @staticmethod
    def send_welcome_email(email: str, first_name: str) -> dict:
        """
        ウェルカムメールを送信
        
        Args:
            email: 送信先メールアドレス
            first_name: ユーザーの名前
        
        Returns:
            {"success": bool, "id": str, "error": str}
        """
        try:
            resend.api_key = settings.RESEND_API_KEY
            
            params = {
                "from": "noreply@yourdomain.com",
                "to": [email],
                "subject": f"Welcome to Our App, {first_name}!",
                "html": UserEmailService._get_welcome_email_html(first_name),
            }
            
            response = resend.Emails.send(params)
            
            return {
                "success": True,
                "id": response["id"],
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            return {
                "success": False,
                "id": None,
                "error": str(e)
            }
    
    @staticmethod
    def _get_welcome_email_html(first_name: str) -> str:
        """ウェルカムメールのHTMLを生成"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    background-color: #4F46E5; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 6px; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome, {first_name}!</h1>
                <p>Thank you for joining our app. We're excited to have you on board!</p>
                <p>
                    <a href="{settings.FRONT_URL}/dashboard" class="button">
                        Get Started
                    </a>
                </p>
                <p>If you have any questions, feel free to reach out to our support team.</p>
                <p>Best regards,<br>The Team</p>
            </div>
        </body>
        </html>
        """
```

---

## Webhook実装

### Webhookエンドポイント

```python
# backend/webhooks/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from common.permissions import IsQStashAuthenticated
from users.services.email_service import UserEmailService

@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="send_welcome_email")
def send_welcome_email_webhook(request):
    """
    QStashから呼ばれるWebhook
    
    ウェルカムメールを送信
    """
    # バリデーション
    serializer = WelcomeEmailWebhookSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    first_name = serializer.validated_data['first_name']
    
    # メール送信
    result = UserEmailService.send_welcome_email(email, first_name)
    
    if not result["success"]:
        raise EmailDeliveryError(
            message=result.get('error', 'Unknown error'),
            email=email
        )
    
    return Response({
        "message": "Email sent successfully",
        "id": result["id"]
    })
```

### Serializer

```python
# backend/webhooks/serializers.py
from rest_framework import serializers

class WelcomeEmailWebhookSerializer(serializers.Serializer):
    """ウェルカムメールWebhookのバリデーション"""
    
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
```

### ルーティング

```python
# backend/webhooks/urls.py
from django.urls import path
from . import views

app_name = 'webhooks'

urlpatterns = [
    path('send-welcome-email', views.send_welcome_email_webhook, name='send_welcome_email'),
    # 他のWebhook
]
```

---

## セキュリティ

### QStash署名検証

```python
# backend/common/permissions.py
import hmac
import hashlib

class IsQStashAuthenticated(BasePermission):
    """
    QStash署名検証
    
    QStashからのリクエストのみを許可
    """
    
    def has_permission(self, request, view):
        signature = request.headers.get('Upstash-Signature')
        
        if not signature:
            return False
        
        return verify_qstash_signature(
            signature=signature,
            body=request.body,
            signing_keys=[
                settings.QSTASH_CURRENT_SIGNING_KEY,
                settings.QSTASH_NEXT_SIGNING_KEY
            ]
        )

def verify_qstash_signature(signature: str, body: bytes, signing_keys: list) -> bool:
    """
    QStash署名を検証
    
    Args:
        signature: Upstash-Signature ヘッダー
        body: リクエストボディ
        signing_keys: 署名キーのリスト
    
    Returns:
        検証結果
    """
    for signing_key in signing_keys:
        expected = hmac.new(
            signing_key.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected):
            return True
    
    return False
```

### レート制限

```python
# backend/users/views.py
from common.decorators import apply_ratelimit

@method_decorator(
    apply_ratelimit(key="ip", rate="3/h", method="POST", block=True),
    name="dispatch"
)
class CustomRegisterView(RegisterView):
    """登録エンドポイントを3回/時間に制限"""
    ...
```

---

## 環境変数設定

### backend/.env

```bash
# QStash（既存）
QSTASH_TOKEN=qstash_xxx
QSTASH_CURRENT_SIGNING_KEY=sig_xxx
QSTASH_NEXT_SIGNING_KEY=sig_xxx

# Resend（新規）
RESEND_API_KEY=re_xxx

# Webhook
WEBHOOK_BASE_URL=https://your-backend.onrender.com

# Frontend（メール内のリンク用）
FRONT_URL=https://your-frontend.pages.dev
```

### settings/base.py

```python
# QStash
QSTASH_TOKEN = env("QSTASH_TOKEN")
QSTASH_CURRENT_SIGNING_KEY = env("QSTASH_CURRENT_SIGNING_KEY")
QSTASH_NEXT_SIGNING_KEY = env("QSTASH_NEXT_SIGNING_KEY")
WEBHOOK_BASE_URL = env("WEBHOOK_BASE_URL")

# Resend
RESEND_API_KEY = env("RESEND_API_KEY")

# Frontend
FRONT_URL = env("FRONT_URL")
```

---

## 開発環境での確認

### 1. ngrokでローカル環境を公開

```bash
# ngrokをインストール
brew install ngrok  # macOS
# または https://ngrok.com/download

# ローカルサーバーを公開（8000番ポート）
ngrok http 8000

# 出力例
Forwarding  https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:8000
```

### 2. 環境変数を更新

```bash
# backend/.env.local
WEBHOOK_BASE_URL=https://xxxx-xxxx-xxxx.ngrok-free.app
```

### 3. ユーザー登録をテスト

```bash
# APIリクエスト
curl -X POST http://localhost:8000/api/v1/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password1": "securepass123",
    "password2": "securepass123",
    "first_name": "John"
  }'
```

### 4. ログを確認

```bash
# Djangoログ
docker compose logs -f backend | grep "welcome_email"

# 成功例
✅ Queued welcome email for test@example.com
✅ Webhook START: send_welcome_email
✅ Email sent successfully: re_xxx

# 失敗例
❌ Failed to send welcome email: Invalid API key
```

### 5. QStash Dashboardで確認

```
1. https://console.upstash.com/qstash にアクセス
2. "Messages" タブで配信状況を確認
3. メッセージID、ステータス、リトライ回数を確認
```

---

## トラブルシューティング

### メールが送信されない

```bash
# 確認項目
1. QStash Webhook が到達しているか
   → QStash Dashboard で確認
   → ログで "Webhook START: send_welcome_email" を確認

2. Resend API Keyが正しいか
   → https://resend.com/api-keys で確認
   → 環境変数 RESEND_API_KEY を再確認

3. Webhook署名検証が成功しているか
   → ログで "Invalid signature" がないか確認
```

### メールが届かない

```bash
# 確認項目
1. スパムフォルダを確認

2. Resend Dashboardでログを確認
   → https://resend.com/emails
   → 送信ステータス、エラーメッセージを確認

3. ドメイン認証を実施（到達率向上）
   → https://resend.com/domains
```

### QStashリトライが動作しない

```bash
# 確認項目
1. Webhook が 200 OK を返しているか
   → 500エラーの場合のみリトライされる

2. リトライ設定を確認
   → QStash Dashboard → Messages → Retry設定
   → 最大3回、5秒間隔（5000 * (retried + 1)）
```

---

## ベストプラクティス

### 1. エラー時も登録を成功させる

```python
# ✅ 良い例
@transaction.atomic
def register_user(self, request, user_data):
    user = self.create_user(...)
    
    # メール送信は副作用として隔離
    if not settings.TESTING:
        transaction.on_commit(
            lambda: self._send_welcome_email_safely(user)
        )
    
    return user  # ユーザー登録は必ず成功

@staticmethod
def _send_welcome_email_safely(user):
    with ErrorMonitor.capture_and_continue(...):
        UserQStashService.send_welcome_email_async(...)
```

### 2. テスト環境での無効化

```python
# settings/base.py
TESTING = False

# tests/conftest.py
@pytest.fixture(autouse=True)
def set_testing_flag(settings):
    settings.TESTING = True

# Service層
if not settings.TESTING:
    transaction.on_commit(lambda: send_email())
```

### 3. メール内容の改善

```python
# ✅ パーソナライズ
subject = f"Welcome to Our App, {first_name}!"

# ✅ CTA（Call To Action）ボタン
<a href="{settings.FRONT_URL}/dashboard" class="button">
    Get Started
</a>

# ✅ 配信停止リンク（将来実装）
<a href="{settings.FRONT_URL}/unsubscribe">Unsubscribe</a>
```

### 4. モニタリング

```python
# QStash Dashboard
→ Messages タブで配信状況を監視

# Resend Dashboard
→ Emails タブで到達率を監視

# ログサービス（Sentry等）
→ EmailDeliveryError を監視
```

---

## まとめ

| 項目 | 実装方法 |
|------|---------|
| **非同期処理** | QStash（自動リトライ） |
| **メール送信** | Resend（高到達率） |
| **セキュリティ** | QStash署名検証 + レート制限 |
| **パフォーマンス** | 3-5倍高速化（非同期化） |
| **テスト** | settings.TESTING で自動無効化 |
| **コスト** | $0/月（無料枠のみ） |

この設計により、以下を実現しています：

✅ **高速なレスポンス**: メール送信を待たずに即座にレスポンス  
✅ **自動リトライ**: QStashが失敗時に自動で再送  
✅ **高い到達率**: Resendによる信頼性の高いメール配信  
✅ **セキュア**: QStash署名検証とレート制限  
✅ **テストフレンドリー**: テスト環境で自動無効化  
✅ **保守性**: レイヤードアーキテクチャで保守容易