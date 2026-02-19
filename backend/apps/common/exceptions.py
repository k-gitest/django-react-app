"""
アプリケーション共通例外クラス
フロントエンド ApiError と連携

情報の三層管理:
1. message: ユーザー向け（フロントエンド表示）
2. data: 開発ヒント（フロントエンド表示・修正可能な情報のみ）
3. internal_info: システム詳細（ログ・Sentryのみ、フロントエンドには返さない）
"""
from typing import Any, Optional


class BaseAppError(Exception):
    """
    アプリケーション全体の基底例外
    
    フロントエンド ApiError との対応:
    - status_code → ApiError.status
    - message → ApiError.serverMessage
    - data → ApiError.data
    - internal_info → ログ・Sentryのみ（フロントエンドには返さない）
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "application_error",
        data: Optional[dict[str, Any]] = None,
        internal_info: Optional[Any] = None  # ログ専用
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.data = data or {}
        self.internal_info = internal_info  # フロントエンドには返さない
        super().__init__(message)


# ============================================================================
# 認証・認可エラー
# ============================================================================
class AuthenticationError(BaseAppError):
    """認証エラー（401）"""
    def __init__(
        self, 
        message: str = "認証に失敗しました", 
        data: Optional[dict] = None,
        internal_info: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            code="authentication_error",
            data=data,
            internal_info=internal_info
        )


class InvalidTokenError(AuthenticationError):
    """トークン検証エラー（401）"""
    def __init__(self, internal_reason: Optional[str] = None):
        super().__init__(
            message="トークンの検証に失敗しました。再度ログインしてください。",
            internal_info=internal_reason  # 詳細はログのみ
        )
        self.code = "invalid_token"


class TokenExpiredError(AuthenticationError):
    """トークン期限切れ（401）"""
    def __init__(self):
        super().__init__(
            message="トークンの有効期限が切れています。再度ログインしてください。"
        )
        self.code = "token_expired"


class AuthorizationError(BaseAppError):
    """認可エラー（403）"""
    def __init__(self, message: str = "この操作を実行する権限がありません"):
        super().__init__(
            message=message,
            status_code=403,
            code="authorization_error"
        )


# ============================================================================
# バリデーションエラー
# ============================================================================
class ValidationError(BaseAppError):
    """バリデーションエラー（400）"""
    def __init__(self, message: str, field: Optional[str] = None):
        data = {"field": field} if field else {}
        super().__init__(message, status_code=400, code="validation_error", data=data)


class UserAlreadyExistsError(BaseAppError):
    """ユーザー重複エラー（409）"""
    def __init__(self, email: str):
        super().__init__(
            message="このメールアドレスは既に登録されています",
            status_code=409,
            code="user_already_exists",
            data={"field": "email"}  # メールアドレス自体は返さない
        )


class ResourceNotFoundError(BaseAppError):
    """リソース未検出（404）"""
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource}が見つかりません"
        super().__init__(
            message=message,
            status_code=404,
            code="resource_not_found",
            data={"resource": resource}
        )


# ============================================================================
# 外部サービスエラー
# ============================================================================
class ExternalServiceError(BaseAppError):
    """外部サービスエラー（503）"""
    def __init__(
        self, 
        service_name: str, 
        user_message: str = "外部サービスとの通信に失敗しました",
        internal_details: Optional[str] = None
    ):
        super().__init__(
            message=f"{service_name}: {user_message}",
            status_code=503,
            code="external_service_error",
            data={"service": service_name},
            internal_info=internal_details  # 詳細はログのみ
        )


class EmailDeliveryError(ExternalServiceError):
    """メール送信エラー"""
    def __init__(self, internal_details: Optional[str] = None):
        super().__init__(
            service_name="メール送信",
            user_message="メールの送信に失敗しました。時間をおいて再度お試しください。",
            internal_details=internal_details
        )
        self.code = "email_delivery_error"


class QStashError(ExternalServiceError):
    """QStashエラー"""
    def __init__(self, internal_details: Optional[str] = None):
        super().__init__(
            service_name="バックグラウンド処理",
            user_message="バックグラウンド処理の実行に失敗しました",
            internal_details=internal_details
        )
        self.code = "qstash_error"


class AnalyticsError(ExternalServiceError):
    """分析サービスエラー（MotherDuck等）"""
    def __init__(self, internal_details: Optional[str] = None):
        super().__init__(
            service_name="分析サービス",
            user_message="分析データの記録に失敗しました",
            internal_details=internal_details
        )
        self.code = "analytics_error"


class EmbeddingError(ExternalServiceError):
    """Gemini Embedding API エラー"""
    def __init__(self, internal_details: Optional[str] = None):
        super().__init__(
            service_name="AI処理",
            user_message="AIによる処理に失敗しました",
            internal_details=internal_details
        )
        self.code = "embedding_error"


class VectorError(ExternalServiceError):
    """Upstash Vector エラー"""
    def __init__(self, internal_details: Optional[str] = None):
        super().__init__(
            service_name="ベクトル検索",
            user_message="検索処理に失敗しました",
            internal_details=internal_details
        )
        self.code = "vector_error"


# ============================================================================
# データベースエラー
# ============================================================================
class DatabaseError(BaseAppError):
    """データベースエラー（500）"""
    def __init__(
        self, 
        user_message: str = "データベースエラーが発生しました",
        internal_details: Optional[str] = None
    ):
        super().__init__(
            message=user_message,
            status_code=500,
            code="database_error",
            internal_info=internal_details  # 詳細はログのみ
        )


class IntegrityConstraintError(DatabaseError):
    """整合性制約違反（409）"""
    def __init__(
        self, 
        constraint_type: str,
        user_hint: str = "リクエストされた操作は、既存のデータと競合するため完了できません",
        internal_details: Optional[str] = None
    ):
        super().__init__(
            user_message=user_hint,
            internal_details=internal_details
        )
        self.status_code = 409
        self.code = "integrity_constraint_error"
        self.data["constraint_type"] = constraint_type  # 抽象的な型のみ