"""
BaseAppError → GraphQLエラー型への変換
DRF custom_exception_handlerに相当
"""
import logging
from typing import Union, Optional
from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_ratelimit.exceptions import Ratelimited

from apps.common.exceptions import (
    BaseAppError,
    UserAlreadyExistsError,
    QStashError,
    AnalyticsError,
    VectorError,
    EmbeddingError,
    EmailDeliveryError,
)
from apps.graphql_api.types.common import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    InternalError,
)

logger = logging.getLogger(__name__)


class ErrorFormatter:
    """
    例外をGraphQLエラー型に変換
    
    既存のDRF custom_exception_handlerと同じ役割
    """
    
    @staticmethod
    def format_exception(
        exc: Exception,
        context: Optional[dict] = None
    ) -> Union[
        ValidationError,
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        ConflictError,
        RateLimitError,
        ExternalServiceError,
        InternalError,
    ]:
        """
        例外をGraphQLエラー型に変換
        
        Args:
            exc: 発生した例外
            context: コンテキスト情報（field_name, operation等）
        
        Returns:
            GraphQLエラー型のインスタンス
        """
        
        # 1. レート制限エラー
        if isinstance(exc, Ratelimited):
            return RateLimitError(
                message="リクエストが多すぎます。しばらく時間を置いてから再度お試しください。",
                retry_after=300,  # 5分
            )
        
        # 2. 認証エラー
        if isinstance(exc, PermissionDenied):
            if "認証" in str(exc) or "ログイン" in str(exc):
                return AuthenticationError(
                    message=str(exc) or "認証が必要です。ログインしてください。"
                )
            else:
                return AuthorizationError(
                    message=str(exc) or "このリソースへのアクセス権限がありません。"
                )
        
        # 3. NotFoundエラー
        if isinstance(exc, Http404):
            return NotFoundError(
                message="リソースが見つかりません。",
                resource_type=context.get("resource_type") if context else None,
                resource_id=context.get("resource_id") if context else None,
            )
        
        # 4. DRF ValidationError
        if isinstance(exc, DRFValidationError):
            # 最初のエラーメッセージを取得
            if isinstance(exc.detail, dict):
                field = list(exc.detail.keys())[0]
                message = exc.detail[field][0] if isinstance(exc.detail[field], list) else str(exc.detail[field])
            else:
                field = None
                message = str(exc.detail[0]) if isinstance(exc.detail, list) else str(exc.detail)
            
            return ValidationError(
                message=message,
                field=field,
            )
        
        # 5. アプリケーション独自例外（BaseAppError）
        if isinstance(exc, BaseAppError):
            return ErrorFormatter._format_base_app_error(exc)
        
        # 6. 予期しないエラー（500）
        logger.exception("Unexpected error in GraphQL resolver")
        
        return InternalError(
            message="サーバー内部で予期しないエラーが発生しました。",
            debug_info=str(exc) if not ErrorFormatter._is_production() else None,
        )
    
    @staticmethod
    def _format_base_app_error(exc: BaseAppError) -> Union[
        ValidationError,
        ConflictError,
        ExternalServiceError,
        InternalError,
    ]:
        """
        BaseAppError派生クラスをGraphQLエラー型に変換
        """
        
        # ユーザー重複エラー
        if isinstance(exc, UserAlreadyExistsError):
            return ConflictError(
                message=exc.message,
                conflicting_field="email",
                code=exc.code,
            )
        
        # 外部サービスエラー
        if isinstance(exc, (QStashError, AnalyticsError, VectorError, EmbeddingError, EmailDeliveryError)):
            service_name_map = {
                QStashError: "QStash",
                AnalyticsError: "MotherDuck",
                VectorError: "Upstash Vector",
                EmbeddingError: "Gemini API",
                EmailDeliveryError: "Resend",
            }
            
            return ExternalServiceError(
                message=ErrorFormatter._user_friendly_message(exc),
                service_name=service_name_map.get(type(exc)),
                code=exc.code,
            )
        
        # バリデーションエラー
        if exc.status_code == 400:
            return ValidationError(
                message=exc.message,
                field=exc.data.get("field") if exc.data else None,
                code=exc.code,
            )
        
        # 内部エラー（500系）
        if exc.status_code >= 500:
            return InternalError(
                message="サーバー内部でエラーが発生しました。",
                code=exc.code,
                debug_info=exc.message if not ErrorFormatter._is_production() else None,
            )
        
        # その他
        return InternalError(
            message=exc.message,
            code=exc.code,
        )
    
    @staticmethod
    def _user_friendly_message(exc: BaseAppError) -> str:
        """
        ユーザー向けのフレンドリーなメッセージに変換
        技術的詳細を隠す
        """
        if isinstance(exc, QStashError):
            return "バックグラウンド処理の開始に失敗しました。"
        elif isinstance(exc, AnalyticsError):
            return "分析データの記録に失敗しました。操作は正常に完了しています。"
        elif isinstance(exc, VectorError):
            return "検索機能でエラーが発生しました。"
        elif isinstance(exc, EmbeddingError):
            return "検索機能の初期化に失敗しました。"
        elif isinstance(exc, EmailDeliveryError):
            return "メール送信に失敗しました。"
        else:
            return exc.message
    
    @staticmethod
    def _is_production() -> bool:
        """本番環境かどうかを判定"""
        from django.conf import settings
        return not settings.DEBUG