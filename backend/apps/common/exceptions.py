"""
アプリケーション共通例外クラス
フロントエンド ApiError と連携
"""
from typing import Any, Optional


class BaseAppError(Exception):
    """
    アプリケーション全体の基底例外
    
    フロントエンド ApiError との対応:
    - status_code → ApiError.status
    - message → ApiError.serverMessage
    - data → ApiError.data
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "application_error",  # フロントエンドでの判定用
        data: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code  # 追加：エラーコード
        self.data = data or {}
        super().__init__(message)


# ドメイン固有の例外
class ValidationError(BaseAppError):
    """バリデーションエラー（400）"""
    def __init__(self, message: str, field: Optional[str] = None):
        data = {"field": field} if field else {}
        super().__init__(message, status_code=400, code="validation_error", data=data)


class UserAlreadyExistsError(ValidationError):
    """ユーザー重複エラー（409）"""
    def __init__(self, email: str):
        super().__init__(
            message=f"メールアドレス {email} は既に登録されています",
            field="email"
        )
        self.status_code = 409  # オーバーライド
        self.code = "user_already_exists"


class ExternalServiceError(BaseAppError):
    """外部サービスエラー（503）"""
    def __init__(self, service_name: str, message: str):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=503,
            code="external_service_error",
            data={"service": service_name}
        )


class EmailDeliveryError(ExternalServiceError):
    """メール送信エラー"""
    def __init__(self, message: str, email: Optional[str] = None):
        super().__init__("Resend", message)
        if email:
            self.data["email"] = email


class QStashError(ExternalServiceError):
    """QStashエラー"""
    def __init__(self, message: str, endpoint: Optional[str] = None):
        super().__init__("QStash", message)
        if endpoint:
            self.data["endpoint"] = endpoint