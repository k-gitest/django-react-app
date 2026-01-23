# エラーハンドリング詳細ガイド

## 目次

- [設計哲学](#設計哲学)
- [エラーハンドリングの階層構造](#エラーハンドリングの階層構造)
- [独自例外クラス](#独自例外クラス)
- [統一エラーハンドラー](#統一エラーハンドラー)
- [Service層のエラーハンドリング](#service層のエラーハンドリング)
- [副作用の隔離](#副作用の隔離)
- [エラープロファイル](#エラープロファイル)
- [階層ごとのエラーハンドリング](#階層ごとのエラーハンドリング)
- [エラーモニタリング統合](#エラーモニタリング統合)
- [フロントエンドとの連携](#フロントエンドとの連携)
- [Webhookのエラーハンドリング](#webhookのエラーハンドリング)
- [テスト環境での無効化](#テスト環境での無効化)
- [ベストプラクティス](#ベストプラクティス)

---

## 設計哲学

本プロジェクトでは、**責務の明確な分離**と**適切な例外の伝播**により、堅牢で保守性の高いエラーハンドリングを実現しています。

```
【原則】
✅ 各層で処理すべきエラーのみを扱う
✅ 例外を適切に翻訳・伝播させる
✅ ユーザーに分かりやすいエラーメッセージを返す
✅ 重要なエラーを確実にモニタリングする

【禁止】
❌ 例外を握りつぶさない
❌ 汎用的すぎるtry-catchを書かない
❌ エラーハンドリングを複数箇所に分散させない
```

---

## エラーハンドリングの階層構造

```
┌─────────────────────────────────────────────────────────────┐
│                  Error Handling Layers                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【View層】                                                  │
│    ├─ 役割: HTTPリクエスト/レスポンスの薄い層               │
│    ├─ エラー処理: 基本的に行わない（統一ハンドラーに委譲） │
│    └─ 例外: そのまま伝播 → custom_exception_handler        │
│                                                             │
│  【Serializer層】                                            │
│    ├─ 役割: リクエストデータのバリデーション                │
│    ├─ エラー処理: DRF標準バリデーション                    │
│    └─ 例外: ValidationError → custom_exception_handler     │
│                                                             │
│  【Service層（親）】                                         │
│    ├─ 役割: ビジネスロジックの統合                          │
│    ├─ エラー処理: @service_error_handler                   │
│    │   └─ Django例外 → アプリケーション独自例外に変換      │
│    └─ 副作用の隔離: ErrorMonitor.capture_and_continue      │
│                                                             │
│  【Service層（子）】                                         │
│    ├─ 役割: 特定ドメインのビジネスロジック                  │
│    ├─ エラー処理: @service_error_handler                   │
│    └─ 例外: そのまま伝播 or 翻訳                            │
│                                                             │
│  【BaseService層（共通基盤）】                               │
│    ├─ 役割: Client層の例外をドメイン例外に翻訳             │
│    ├─ エラー処理: try-catch で翻訳                         │
│    └─ 例外: QStashError, AnalyticsError, etc.              │
│                                                             │
│  【Infrastructure層（Client）】                              │
│    ├─ 役割: 外部サービスとの純粋な通信                      │
│    ├─ エラー処理: 基本的に行わない                         │
│    └─ 例外: requests.RequestException, etc.（生のまま）    │
│                                                             │
│  【統一エラーハンドラー】                                    │
│    ├─ custom_exception_handler（DRF）                      │
│    │   ├─ BaseAppError → JSON変換                         │
│    │   ├─ Ratelimited → 429 Too Many Requests             │
│    │   └─ 未ハンドリング例外 → 500 Internal Server Error  │
│    │                                                        │
│    └─ ErrorMonitor（ログサービス統合）                      │
│        ├─ 重要なエラーを自動報告                            │
│        ├─ コンテキスト情報を付与                            │
│        └─ タグ・フィンガープリントで分類                    │
│        （※詳細は error-monitoring.md 参照）                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 独自例外クラス

### 基底クラス: BaseAppError

```python
class BaseAppError(Exception):
    """
    アプリケーション全体の基底例外
    
    フロントエンド ApiError との対応:
    - status_code → ApiError.status
    - message → ApiError.serverMessage
    - code → ApiError での判定用
    - data → ApiError.data
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "application_error",
        data: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.data = data or {}
        super().__init__(message)
```

### 派生クラス一覧

| 例外クラス | 用途 | ステータスコード | code |
|-----------|------|----------------|------|
| **ValidationError** | バリデーションエラー | 400 | `validation_error` |
| **UserAlreadyExistsError** | ユーザー重複 | 409 | `user_already_exists` |
| **ExternalServiceError** | 外部サービスエラー | 503 | `external_service_error` |
| **EmailDeliveryError** | メール送信失敗 | 503 | `external_service_error` |
| **QStashError** | QStash通信失敗 | 503 | `external_service_error` |
| **AnalyticsError** | 分析サービスエラー | 503 | `analytics_error` |
| **EmbeddingError** | Gemini API エラー | 503 | `embedding_error` |
| **VectorError** | Upstash Vector エラー | 503 | `vector_error` |

### 使用例

```python
# バリデーションエラー
raise ValidationError(
    message="無効なメールアドレスです",
    field="email"
)

# ユーザー重複エラー
raise UserAlreadyExistsError(email="user@example.com")

# 外部サービスエラー
raise QStashError(
    message="Connection timeout",
    endpoint="/api/v1/webhooks/send-welcome-email"
)
```

---

## 統一エラーハンドラー

### custom_exception_handler（DRF統合）

すべてのAPI例外を統一形式で処理します。

**レスポンス形式**:
```json
{
  "error": "エラーコード",      // フロントエンド ApiError での判定用
  "detail": "エラーメッセージ",  // ApiError.serverMessage
  "data": {...}                  // ApiError.data（オプション）
}
```

**処理フロー**:

```python
def custom_exception_handler(exc, context):
    # 1. レート制限（429）
    if isinstance(exc, Ratelimited):
        return Response({
            "error": "rate_limit_exceeded",
            "detail": "リクエストが多すぎます。..."
        }, status=429)
    
    # 2. アプリケーション独自例外
    if isinstance(exc, BaseAppError):
        # 500エラーのみログサービスに送信
        if exc.status_code >= 500:
            ErrorMonitor.log_error(exc, ...)
        
        return Response({
            "error": exc.code,
            "detail": exc.message,
            "data": exc.data  # オプション
        }, status=exc.status_code)
    
    # 3. DRF標準例外処理
    response = exception_handler(exc, context)
    
    # 4. 未ハンドリング例外（500）
    if response is None:
        ErrorMonitor.log_error(exc, ...)  # 必ず送信
        return Response({
            "error": "internal_server_error",
            "detail": "サーバー内部で予期しないエラーが発生しました。"
        }, status=500)
    
    return response
```

---

## Service層のエラーハンドリング

### @service_error_handler デコレーター

Service層の全メソッドに適用し、Django例外を独自例外に自動変換します。

```python
@service_error_handler
def create_todo(user, validated_data):
    # ビジネスロジック
    todo = Todo.objects.create(user=user, **validated_data)
    return todo

# デコレーターが自動処理:
# ✅ IntegrityError → BaseAppError（メール重複の場合は UserAlreadyExistsError）
# ✅ 予期しないエラー → ログサービスに自動送信 + 再送出
# ✅ BaseAppError → ログ出力 + 再送出
```

**デコレーターの役割**:

| 例外タイプ | 処理 |
|-----------|------|
| **BaseAppError** | ログ出力 → 再送出 |
| **IntegrityError（メール重複）** | UserAlreadyExistsError に変換 → 送出 |
| **IntegrityError（その他）** | ログサービスに送信 → BaseAppError に変換 → 送出 |
| **予期しないエラー** | ログサービスに送信 → ログ出力 → 再送出 |

---

## 副作用の隔離

### ErrorMonitor.capture_and_continue

**設計原則**: メインフロー（DB保存等）の成功を保証しながら、副作用（メール送信、分析ログ等）の失敗を隔離する。

```python
# 例: ユーザー登録時のウェルカムメール送信
@transaction.atomic
def register_user(self, request, user_data: Dict) -> CustomUser:
    # 1. ユーザー作成（絶対に成功させる）
    user = self.command_service.create_user_with_adapter(...)
    
    # 2. 副作用を予約（DB保存成功後に実行）
    if not settings.TESTING:
        transaction.on_commit(lambda: self._send_welcome_email_safely(user))
        transaction.on_commit(lambda: self._log_registration_safely(user, request))
    
    return user

@staticmethod
def _send_welcome_email_safely(user: CustomUser):
    """ウェルカムメール送信を安全に実行（失敗してもエラーを投げない）"""
    with ErrorMonitor.capture_and_continue(
        component='qstash',
        operation='send_welcome_email',
        service='UserRegistrationService',
        expected_errors=(QStashError,),
        profile=ErrorProfiles.INFRASTRUCTURE_MEDIUM,
        user=user,
        context={'email': user.email}
    ):
        UserQStashService.send_welcome_email_async(...)
```

### capture_and_continue の仕組み

```
with ErrorMonitor.capture_and_continue(...):
    副作用の実行（メール送信、分析ログ等）

↓

【期待されるエラー（expected_errors）】
    → warning レベルでログ出力
    → ログサービスに送信（グループ化）
    → 処理を継続（エラーを再送出しない）

【予期しないエラー】
    → error レベルでログ出力
    → ログサービスに送信（重要度: high）
    → 処理を継続（エラーを再送出しない）
```

### 使い方の例

```python
# ✅ 単一の例外クラス（最もシンプル）
with ErrorMonitor.capture_and_continue(
    component='qstash',
    operation='send_welcome_email',
    service='UserRegistrationService',
    expected_errors=QStashError,  # カンマ不要
    profile=ErrorProfiles.INFRASTRUCTURE_MEDIUM,
    user=user
):
    UserQStashService.send_welcome_email_async(...)

# ✅ 複数の例外クラス
with ErrorMonitor.capture_and_continue(
    component='payment',
    operation='process_payment',
    service='PaymentService',
    expected_errors=(PaymentError, TimeoutError),
    profile=ErrorProfiles.EXTERNAL_SERVICE_HIGH,
    user=user
):
    process_payment(...)
```

---

## エラープロファイル

よく使うエラー特性をプリセット化し、一貫性のあるエラー報告を実現します。

```python
class ErrorProfiles:
    # インフラ系（QStash, Email等）
    INFRASTRUCTURE_MEDIUM = ErrorProfile(
        error_category='infrastructure',
        severity='medium',
        user_impact='low',
        business_critical='false',
        use_fingerprint=True  # グループ化する
    )
    
    INFRASTRUCTURE_HIGH = ErrorProfile(
        error_category='infrastructure',
        severity='high',
        user_impact='medium',
        business_critical='false',
        use_fingerprint=True
    )
    
    # 監視系（Analytics等）
    MONITORING_LOW = ErrorProfile(
        error_category='monitoring',
        severity='low',
        user_impact='none',
        business_critical='false',
        use_fingerprint=True
    )
    
    # 外部サービス
    EXTERNAL_SERVICE_HIGH = ErrorProfile(
        error_category='external_service',
        severity='high',
        user_impact='high',
        business_critical='true',
        use_fingerprint=False  # グループ化しない
    )
```

**プロファイルの効果**:

| プロファイル | use_fingerprint | ログサービスでの挙動 |
|-------------|----------------|-------------------|
| **INFRASTRUCTURE_MEDIUM** | ✅ true | 同じサービス・操作のエラーをグループ化 |
| **MONITORING_LOW** | ✅ true | 同じサービス・操作のエラーをグループ化 |
| **EXTERNAL_SERVICE_HIGH** | ❌ false | 各エラーを個別に記録（詳細な追跡） |

---

## 階層ごとのエラーハンドリング

### 1. View層

```python
@method_decorator(
    apply_ratelimit(key="ip", rate="5/5m", method="POST", block=True),
    name="dispatch"
)
class CustomLoginView(LoginView):
    """
    View層ではエラー処理を行わない
    
    ✅ 例外はそのまま伝播 → custom_exception_handler が処理
    ❌ try-catch を書かない
    """
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            user = self._get_user_from_response(response)
            if user:
                UserAuthService.handle_login_success(user, request)
        
        return response
```

---

### 2. Serializer層

```python
class CustomRegisterSerializer(RegisterSerializer):
    """
    Serializer層では DRF 標準バリデーションのみ
    
    ✅ DRF の ValidationError を使用
    ❌ 独自例外を送出しない
    """
    
    def save(self, request):
        cleaned_data = self.get_cleaned_data()
        
        # サービス層を呼び出すだけ（エラー処理は統一ハンドラーに委譲）
        user = self.registration_service.register_user(
            request=request,
            user_data=cleaned_data
        )
        
        return user
```

---

### 3. Service層（親）

```python
class UserRegistrationService:
    """
    親Service: ビジネスロジックの統合
    
    ✅ @service_error_handler で Django例外を自動変換
    ✅ 副作用は ErrorMonitor.capture_and_continue で隔離
    """
    
    @service_error_handler
    @transaction.atomic
    def register_user(self, request, user_data: Dict) -> CustomUser:
        email = user_data.get('email')
        
        # メールアドレスの重複チェック
        if self.query_service.email_exists(email):
            raise UserAlreadyExistsError(email=email)
        
        # ユーザー作成
        user = self.command_service.create_user_with_adapter(...)
        
        # 副作用を予約（DB保存成功後に実行）
        if not settings.TESTING:
            transaction.on_commit(lambda: self._send_welcome_email_safely(user))
            transaction.on_commit(lambda: self._log_registration_safely(user, request))
        
        return user
    
    @staticmethod
    def _send_welcome_email_safely(user: CustomUser):
        """副作用を安全に実行（失敗してもエラーを投げない）"""
        with ErrorMonitor.capture_and_continue(
            component='qstash',
            operation='send_welcome_email',
            service='UserRegistrationService',
            expected_errors=(QStashError,),
            profile=ErrorProfiles.INFRASTRUCTURE_MEDIUM,
            user=user
        ):
            UserQStashService.send_welcome_email_async(...)
```

---

### 4. Service層（子）

```python
class UserQStashService(BaseQStashService):
    """
    子Service: 特定ドメインのビジネスロジック
    
    ✅ @service_error_handler で例外を自動変換
    ✅ BaseService を呼び出すだけ
    """
    
    ENDPOINT_WELCOME_EMAIL: Final = "/api/v1/webhooks/send-welcome-email"
    
    @classmethod
    @service_error_handler
    def send_welcome_email_async(cls, email: str, first_name: str) -> str:
        """ウェルカムメール送信をキューに追加"""
        return cls._safe_publish(
            cls.ENDPOINT_WELCOME_EMAIL,
            {"email": email, "first_name": first_name}
        )
```

---

### 5. BaseService層（共通基盤）

```python
class BaseQStashService:
    """
    共通基盤: Client層の例外をドメイン例外に翻訳
    
    ✅ Client層の例外を QStashError に変換
    ❌ @service_error_handler は使わない（手動でtry-catch）
    """
    
    @classmethod
    def _safe_publish(
        cls, 
        endpoint_path: str, 
        payload: dict, 
        delay_seconds: int = 0
    ) -> str:
        try:
            message_id = QStashClient.publish(endpoint_path, payload, delay_seconds)
            
            if not message_id or not isinstance(message_id, str):
                raise QStashError(
                    message="Invalid response from QStash client",
                    endpoint=endpoint_path
                )
            
            return message_id
            
        except QStashError:
            # 既に適切な例外なので再送出
            raise
        except Exception as e:
            # Client層の例外を QStashError に変換
            raise QStashError(
                message=f"QStash operation failed: {str(e)}",
                endpoint=endpoint_path
            ) from e
```

---

### 6. Infrastructure層（Client）

```python
class QStashClient:
    """
    Client: 外部サービスとの純粋な通信
    
    ✅ 例外は発生させたまま（翻訳しない）
    ❌ エラーハンドリングを行わない
    """
    
    @staticmethod
    def publish(endpoint_path: str, payload: dict, delay_seconds: int = 0) -> str:
        """QStashにメッセージを送信"""
        webhook_url = f"{settings.WEBHOOK_BASE_URL}{endpoint_path}"
        
        headers = {
            "Authorization": f"Bearer {settings.QSTASH_TOKEN}",
            "Content-Type": "application/json",
        }
        
        if delay_seconds > 0:
            headers["Upstash-Delay"] = f"{delay_seconds}s"
        
        # エラーハンドリングを行わない（requests.RequestException をそのまま発生）
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

## エラーモニタリング統合

`ErrorMonitor` クラスは、Sentry等のログサービスへの報告を抽象化します。実装の切り替えはこのクラス内部で行うため、アプリケーションコードは具体的なログサービスに依存しません。

**注**: ErrorMonitor の具体的な実装・設定については、[error-monitoring.md](error-monitoring.md) を参照してください。

### ErrorMonitor の主要メソッド

```python
class ErrorMonitor:
    """エラーモニタリング統合（実装は抽象化）"""
    
    @staticmethod
    def log_error(
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        user=None,
        fingerprint: Optional[list] = None
    ):
        """エラーをログサービスに報告"""
        ...
    
    @staticmethod
    def log_warning(message: str, ...):
        """警告をログサービスに報告"""
        ...
    
    @staticmethod
    def log_info(message: str, ...):
        """情報をログサービスに報告"""
        ...
    
    @staticmethod
    @contextmanager
    def capture_and_continue(...):
        """副作用の失敗を隔離（処理は継続）"""
        ...
```

### タグとコンテキスト

ログサービスで効果的にエラーをフィルタリング・検索するため、タグとコンテキストを活用します。

**タグ（検索・フィルタリング用）**:

```python
tags = {
    'component': 'qstash',              # コンポーネント名
    'error_category': 'infrastructure', # エラーカテゴリ
    'severity': 'medium',               # 重要度
    'user_impact': 'low',               # ユーザー影響度
    'business_critical': 'false',       # ビジネスクリティカル
}
```

**コンテキスト（詳細情報用）**:

```python
context = {
    'service': 'UserRegistrationService',
    'operation': 'send_welcome_email',
    'email': 'user@example.com',
    'step': 'qstash_publish',
}
```

---

## フロントエンドとの連携

### ApiError クラス（フロントエンド）

```typescript
class ApiError extends Error {
  constructor(
    public status: number,
    public serverMessage: string,
    public code?: string,
    public data?: Record<string, unknown>
  ) {
    super(serverMessage);
  }
}
```

### エラーレスポンス形式

```json
{
  "error": "user_already_exists",
  "detail": "メールアドレス user@example.com は既に登録されています",
  "data": {
    "field": "email"
  }
}
```

### フロントエンドでの処理

```typescript
try {
  await registerUser(data);
} catch (error) {
  if (error instanceof ApiError) {
    if (error.code === 'user_already_exists') {
      // メールアドレス重複エラーの処理
      toast.error(error.serverMessage);
    } else if (error.code === 'validation_error') {
      // バリデーションエラーの処理
      toast.error(error.serverMessage);
    } else {
      // その他のエラー
      toast.error('エラーが発生しました');
    }
  }
}
```

---

## Webhookのエラーハンドリング

```python
@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="send_welcome_email")
def send_welcome_email_webhook(request):
    """
    Webhook では統一エラーハンドラーに完全に委譲
    
    ✅ Serializer で バリデーション
    ✅ Service で ビジネスロジック実行
    ✅ 例外はそのまま伝播 → custom_exception_handler が処理
    """
    # バリデーション
    serializer = WelcomeEmailWebhookSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    first_name = serializer.validated_data['first_name']
    
    # メール送信（エラーは統一エラーハンドラーが処理）
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

### @log_webhook_call デコレーター

```python
def log_webhook_call(webhook_name: str):
    """Webhook呼び出しのロギング"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            logger.info(f"Webhook START: {webhook_name}")
            
            try:
                response = func(request, *args, **kwargs)
                logger.info(f"Webhook END: {webhook_name} Status: {response.status_code}")
                return response
            except Exception as e:
                logger.error(f"Webhook FAILED: {webhook_name} Error: {str(e)}")
                # Webhook失敗はログサービスに送信
                ErrorMonitor.log_error(
                    exception=e,
                    context={'webhook': webhook_name, ...},
                    tags={'component': 'webhook', 'severity': 'high', ...},
                    fingerprint=['WebhookHandler', webhook_name, 'webhook']
                )
                raise
        return wrapper
    return decorator
```

---

## テスト環境での無効化

開発・テスト効率を保つため、特定の機能をテスト環境で自動無効化します。

### 1. レート制限

```python
def apply_ratelimit(**kwargs):
    """テスト環境ではレート制限をスキップ"""
    def decorator(func):
        if getattr(settings, "TESTING", False):
            return func
        return ratelimit(**kwargs)(func)
    return decorator
```

### 2. 非同期タスク

```python
if not settings.TESTING:
    transaction.on_commit(lambda: self._send_welcome_email_safely(user))
    transaction.on_commit(lambda: self._log_registration_safely(user, request))
```

### 3. ログサービス送信

```python
def _before_send(event: Dict, hint: Dict) -> Optional[Dict]:
    """ログサービス送信前の前処理"""
    if getattr(settings, 'TESTING', False):
        return None  # テスト時は送信しない
    
    # ... その他の処理
    
    return event
```

---

## ベストプラクティス

### ✅ やるべきこと

1. **各層で適切な責務を持つ**
   - View: エラー処理しない
   - Serializer: DRF標準バリデーションのみ
   - Service: ビジネスロジックのエラー処理
   - Client: エラーハンドリングしない

2. **例外を適切に翻訳する**
   ```python
   # BaseService層で Client例外 → ドメイン例外 に変換
   except Exception as e:
       raise QStashError(
           message=f"QStash operation failed: {str(e)}",
           endpoint=endpoint_path
       ) from e
   ```

3. **副作用を隔離する**
   ```python
   with ErrorMonitor.capture_and_continue(...):
       UserQStashService.send_welcome_email_async(...)
   ```

4. **重要なエラーをモニタリングする**
   ```python
   ErrorMonitor.log_error(
       exception=e,
       context={...},
       tags={...},
       user=user
   )
   ```

---

### ❌ やってはいけないこと

1. **例外を握りつぶす**
   ```python
   # ❌ 悪い例
   try:
       some_operation()
   except Exception:
       pass  # 握りつぶし
   ```

2. **汎用的すぎるtry-catch**
   ```python
   # ❌ 悪い例
   try:
       # 多くの処理
       ...
   except Exception as e:
       logger.error(f"Error: {e}")
       # どこでエラーが発生したか分からない
   ```

3. **複数箇所でのエラーハンドリング**
   ```python
   # ❌ 悪い例: View でも Service でもエラー処理
   def post(self, request):
       try:
           result = service.do_something()
       except SomeError:
           return Response({"error": "..."})
   
   @service_error_handler
   def do_something(self):
       try:
           # ...
       except SomeError:
           # ここでも処理
   ```

4. **エラーメッセージの重複**
   ```python
   # ❌ 悪い例
   raise BaseAppError("QStash operation failed: Connection timeout")
   # ↓ custom_exception_handler で
   return Response({"detail": "QStash operation failed: Connection timeout"})
   # ↓ フロントエンドで
   toast.error("QStash operation failed: Connection timeout")
   # → ユーザーに技術的な詳細が見える
   
   # ✅ 良い例
   raise QStashError(
       message="Connection timeout",
       endpoint=endpoint_path
   )
   # → custom_exception_handler が適切なメッセージに変換
   # → フロントエンドで "メール送信に失敗しました" と表示
   ```

---

## まとめ

| 層 | 責務 | エラー処理 |
|---|------|-----------|
| **View** | HTTPリクエスト/レスポンス | 行わない（統一ハンドラーに委譲） |
| **Serializer** | バリデーション | DRF標準バリデーションのみ |
| **Service（親）** | ビジネスロジックの統合 | @service_error_handler + capture_and_continue |
| **Service（子）** | ドメインロジック | @service_error_handler |
| **BaseService** | 例外の翻訳 | try-catch で Client例外 → ドメイン例外 |
| **Client** | 外部サービス通信 | 行わない（例外をそのまま発生） |
| **統一ハンドラー** | 最終的なエラー処理 | すべての例外をJSON形式で返却 + ログサービス送信 |

この設計により、以下を実現しています：

✅ **責務の明確な分離**: 各層が適切な責務のみを持つ  
✅ **適切な例外の伝播**: エラーが適切に上位層に伝わる  
✅ **副作用の隔離**: メインフローの成功を保証  
✅ **効果的なモニタリング**: 重要なエラーを確実に追跡  
✅ **ユーザーフレンドリー**: 分かりやすいエラーメッセージ  
✅ **保守性の高さ**: 一貫性のあるエラーハンドリング