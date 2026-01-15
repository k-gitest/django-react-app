"""
DRF統一エラーハンドラー
フロントエンド errorHandler と連携
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status as http_status
from django_ratelimit.exceptions import Ratelimited
from .exceptions import BaseAppError
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    統一エラーハンドラー
    
    フロントエンドへのレスポンス形式:
    {
        "error": "エラーコード",      // ApiError での判定用
        "detail": "エラーメッセージ",  // ApiError.serverMessage
        "data": {...}                  // ApiError.data
    }
    """
    
    # 1. レート制限
    if isinstance(exc, Ratelimited):
        logger.warning(
            "Rate limit exceeded",
            extra={
                'view': context.get('view').__class__.__name__,
                'path': context.get('request').path
            }
        )
        return Response(
            {
                "error": "rate_limit_exceeded",
                "detail": "リクエストが多すぎます。しばらく時間を置いてから再度お試しください。"
            },
            status=http_status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # 2. アプリケーション独自例外
    if isinstance(exc, BaseAppError):
        response_data = {
            "error": exc.code,
            "detail": exc.message
        }
        
        if exc.data:
            response_data["data"] = exc.data
        
        return Response(response_data, status=exc.status_code)
    
    # 3. DRF標準の例外処理
    response = exception_handler(exc, context)
    
    # 4. 未ハンドリングの例外（500エラー）
    if response is None:
        logger.critical(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                'view': context.get('view').__class__.__name__,
                'exception_type': exc.__class__.__name__
            }
        )
        return Response(
            {
                "error": "internal_server_error",
                "detail": "サーバー内部で予期しないエラーが発生しました。"
            },
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # DRFの標準レスポンスを統一形式に変換
    if isinstance(response.data, dict):
        if "detail" not in response.data:
            response.data = {
                "error": "unknown_error",
                "detail": str(response.data)
            }
        else:
            response.data = {
                "error": response.data.get("detail", "unknown_error"),
                "detail": response.data.get("detail", "エラーが発生しました")
            }
    
    return response