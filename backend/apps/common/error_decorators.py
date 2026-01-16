"""
共通デコレーター（シンプル版）
"""
import functools
import logging
from django.db import IntegrityError
from .exceptions import BaseAppError, UserAlreadyExistsError

logger = logging.getLogger(__name__)


def service_error_handler(func):
    """
    Service層のエラーハンドリング
    
    - Django例外を独自例外に変換
    - 自動ログ出力
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 可能な限りクラス名を取得。取れない場合はモジュール名や "Function" を設定
        if args and hasattr(args[0], '__class__') and not isinstance(args[0], (str, dict, list)):
            service_name = args[0].__class__.__name__
        else:
            service_name = "ServiceFunction"

        operation = func.__name__
        
        try:
            return func(*args, **kwargs)
            
        except BaseAppError:
            # 既に独自例外なら、ログ出力して再送出
            logger.warning(
                f"{service_name}.{operation} failed",
                exc_info=True,
                extra={'service': service_name, 'operation': operation}
            )
            raise
            
        except IntegrityError as e:
            # メールアドレス重複を判定
            error_msg = str(e).lower()
            if "unique" in error_msg and "email" in error_msg:
                logger.warning(
                    f"{service_name}.{operation}: Duplicate email",
                    extra={'service': service_name, 'operation': operation}
                )
                raise UserAlreadyExistsError(email="(詳細不明)")
            
            # その他のIntegrityError
            logger.error(
                f"{service_name}.{operation}: Database integrity error",
                exc_info=True
            )
            raise BaseAppError(
                "データベース制約エラーが発生しました",
                code="database_error"
            )
            
        except Exception as e:
            # 予期しないエラー
            logger.exception(
                f"{service_name}.{operation}: Unexpected error",
                extra={'service': service_name, 'operation': operation}
            )
            raise
            
    return wrapper

def log_webhook_call(webhook_name: str):
    """Webhook呼び出しのロギング"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            logger.info(
                f"Webhook START: {webhook_name}",
                extra={
                    'webhook': webhook_name,
                    'remote_addr': request.META.get('REMOTE_ADDR'),
                }
            )

            try:
                response = func(request, *args, **kwargs)
                # 終了時もログ出力（ステータスコード付き）
                logger.info(f"Webhook END: {webhook_name} Status: {response.status_code}")
                return response
            except Exception as e:
                # 失敗時もログ出力
                logger.error(f"Webhook FAILED: {webhook_name} Error: {str(e)}")
                raise
        return wrapper
    return decorator