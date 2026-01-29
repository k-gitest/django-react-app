"""
GraphQL統一エラーハンドラー
DRFのcustom_exception_handlerに相当
"""
import logging
from typing import Any, Optional
from functools import wraps

from apps.common.exceptions import BaseAppError
from apps.common.error_reporting import ErrorMonitor
from apps.graphql_api.errors.formatters import ErrorFormatter

logger = logging.getLogger(__name__)


def graphql_error_handler(func):
    """
    GraphQL Resolver用のエラーハンドリングデコレーター
    
    Service層の @service_error_handler と同じ役割
    ただし、GraphQLでは例外を送出せず、Union型のエラーを返す
    
    使用例:
        @strawberry.mutation
        @graphql_error_handler
        def create_todo(self, info, input):
            # ビジネスロジック
            return TodoCommandService.create_todo(...)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        
        except BaseAppError as e:
            # アプリケーション独自例外
            logger.warning(
                f"GraphQL resolver error: {e.__class__.__name__}",
                extra={
                    'resolver': func.__name__,
                    'error_code': e.code,
                    'status_code': e.status_code,
                }
            )
            
            # 500エラーのみログサービスに送信
            if e.status_code >= 500:
                ErrorMonitor.log_error(
                    exception=e,
                    context={
                        'resolver': func.__name__,
                        'graphql': True,
                    },
                    tags={
                        'component': 'graphql',
                        'error_code': e.code,
                    }
                )
            
            # GraphQLエラー型に変換して返す
            return ErrorFormatter.format_exception(e)
        
        except Exception as e:
            # 予期しないエラー
            logger.exception(f"Unexpected error in GraphQL resolver: {func.__name__}")
            
            # ログサービスに送信
            ErrorMonitor.log_error(
                exception=e,
                context={
                    'resolver': func.__name__,
                    'graphql': True,
                },
                tags={
                    'component': 'graphql',
                    'severity': 'high',
                }
            )
            
            # GraphQLエラー型に変換して返す
            return ErrorFormatter.format_exception(e)
    
    return wrapper


class GraphQLErrorContext:
    """
    GraphQL Resolverのコンテキスト情報を収集
    ErrorFormatterに渡す
    """
    
    @staticmethod
    def get_context(info, **kwargs) -> dict:
        """
        Resolverのコンテキスト情報を取得
        
        Args:
            info: strawberry.Info
            **kwargs: 追加のコンテキスト情報
        
        Returns:
            コンテキスト辞書
        """
        context = {
            'field_name': info.field_name,
            'operation': info.operation.operation.value,  # 'query' or 'mutation'
            'path': info.path.as_list(),
        }
        
        # 追加のコンテキスト情報をマージ
        context.update(kwargs)
        
        return context