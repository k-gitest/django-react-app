"""
Sentry統合ユーティリティ
"""
import logging
from typing import Optional, Dict, Any
import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from django.conf import settings

logger = logging.getLogger(__name__)


def before_send_sentry(event: Dict, hint: Dict) -> Optional[Dict]:
    """
    Sentryにイベントを送信する前の前処理
    
    - 機密情報のフィルタリング
    - テスト環境での送信抑制
    - エラーの優先度付け
    
    Args:
        event: Sentryイベントデータ
        hint: エラーの追加情報
        
    Returns:
        処理後のイベント（Noneを返すと送信されない）
    """
    # テスト環境では送信しない
    if getattr(settings, 'TESTING', False):
        return None
    
    # 特定のエラーは送信しない（ノイズ削減）
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # 404エラーは送信しない
        if exc_type.__name__ == 'Http404':
            return None
        
        # レート制限エラーは送信しない（意図的なエラー）
        if exc_type.__name__ == 'Ratelimited':
            return None
    
    # パスワードなど機密情報のマスキング
    if 'request' in event:
        request_data = event['request']
        if 'data' in request_data:
            for key in ['password', 'password1', 'password2', 'token']:
                if key in request_data['data']:
                    request_data['data'][key] = '***REDACTED***'
    
    return event


def capture_exception_with_context(
    exception: Exception,
    level: str = 'error',
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    user_info: Optional[Dict[str, Any]] = None
):
    """
    コンテキスト情報付きでSentryに例外を送信
    
    Args:
        exception: 送信する例外
        level: ログレベル ('error', 'warning', 'info')
        extra: 追加のコンテキスト情報
        tags: タグ情報（検索・フィルタリング用）
        user_info: ユーザー情報
    
    Example:
        capture_exception_with_context(
            exception=e,
            level='error',
            extra={
                'service': 'UserRegistrationService',
                'operation': 'register_user',
                'email': user.email
            },
            tags={
                'component': 'authentication',
                'error_type': 'email_delivery'
            },
            user_info={
                'id': user.id,
                'email': user.email
            }
        )
    """
    with sentry_sdk.push_scope() as scope:
        # レベル設定
        scope.level = level
        
        # 追加コンテキスト
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        
        # タグ設定
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        
        # ユーザー情報
        if user_info:
            scope.set_user(user_info)
        
        # 例外を送信
        capture_exception(exception)


def capture_message_with_context(
    message: str,
    level: str = 'info',
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None
):
    """
    コンテキスト情報付きでSentryにメッセージを送信
    
    Args:
        message: 送信するメッセージ
        level: ログレベル
        extra: 追加のコンテキスト情報
        tags: タグ情報
    """
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        
        capture_message(message)


class ErrorMonitor:
    """
    Sentryへのログ送信を簡略化するクラス
    """
    
    @staticmethod
    def log_error(
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user=None
    ):
        """
        エラーレベルのログをSentryに送信
        
        Args:
            exception: 例外オブジェクト
            context: コンテキスト情報
            user: Userオブジェクト
        """
        user_info = None
        if user and hasattr(user, 'id'):
            user_info = {
                'id': user.id,
                'email': getattr(user, 'email', None),
            }
        
        capture_exception_with_context(
            exception=exception,
            level='error',
            extra=context,
            user_info=user_info
        )
    
    @staticmethod
    def log_warning(
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """警告レベルのログをSentryに送信"""
        capture_message_with_context(
            message=message,
            level='warning',
            extra=context
        )