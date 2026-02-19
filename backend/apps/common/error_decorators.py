"""
共通デコレーター
"""
import functools
import logging
from django.db import IntegrityError as DjangoIntegrityError
from .exceptions import BaseAppError, UserAlreadyExistsError, IntegrityConstraintError
from .error_reporting import ErrorMonitor

logger = logging.getLogger(__name__)


def service_error_handler(func):
    """
    Service層のエラーハンドリング
    
    - Django例外を独自例外に変換
    - 自動ログ出力
    - 重要なエラーをSentryに送信
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
            
        except BaseAppError as exc:
            # 既に独自例外なら、ログ出力して再送出
            # internal_info をログに出力
            if hasattr(exc, 'internal_info') and exc.internal_info:
                logger.warning(
                    f"{service_name}.{operation}: Internal details: {exc.internal_info}",
                    extra={'service': service_name, 'operation': operation}
                )
            raise
            
        except DjangoIntegrityError as e:
            error_msg = str(e).lower()
            
            # メールアドレス重複
            if "unique" in error_msg and "email" in error_msg:
                logger.warning(
                    f"{service_name}.{operation}: Duplicate email: {str(e)}",
                    extra={'service': service_name, 'operation': operation}
                )
                raise UserAlreadyExistsError(email="")  # メールアドレスは返さない
            
            # その他のユニーク制約違反
            if "unique" in error_msg:
                constraint_type = "unknown_unique_constraint"
                if "oidc_sub" in error_msg:
                    constraint_type = "oidc_sub"
                
                logger.error(
                    f"{service_name}.{operation}: Unique constraint violation: {str(e)}",
                    extra={'service': service_name, 'operation': operation}
                )
                raise IntegrityConstraintError(
                    constraint_type=constraint_type,
                    user_hint='データの重複エラーが発生しました',
                    internal_details=str(e)  # ← ログ・Sentryのみ
                )
            
            # その他のIntegrityError
            logger.error(
                f"{service_name}.{operation}: Database integrity error: {str(e)}",
                exc_info=False
            )
            ErrorMonitor.log_error(
                exception=e,
                context={
                    'service': service_name,
                    'operation': operation,
                    'error_type': 'database_integrity',
                    'error_details': str(e)  # Sentryには詳細を送る
                },
                tags={
                    'component': 'database',
                    'error_category': 'unexpected',
                    'severity': 'high',
                    'service': service_name
                },
                fingerprint=[service_name, operation, 'database']
            )
            raise IntegrityConstraintError(
                constraint_type='unknown',
                user_hint='データベースエラーが発生しました',
                internal_details=str(e)  # ← ログ・Sentryのみ
            )
            
        except Exception as e:
            # 予期しないエラー
            logger.exception(
                f"{service_name}.{operation}: Unexpected error",
                extra={'service': service_name, 'operation': operation}
            )
            # Sentryに送信（予期しないエラーは必ず送信）
            ErrorMonitor.log_error(
                exception=e,
                context={
                    'service': service_name,
                    'operation': operation,
                    'error_type': 'unexpected'
                },
                tags={
                    'component': 'service',
                    'error_category': 'unexpected',
                    'severity': 'critical',
                    'service': service_name
                },
                fingerprint=None  # 予期しないエラーはグループ化しない
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
                # Webhook失敗はSentryに送信（外部からのトリガー）
                ErrorMonitor.log_error(
                    exception=e,
                    context={
                        'webhook': webhook_name,
                        'remote_addr': request.META.get('REMOTE_ADDR'),
                    },
                    tags={
                        'component': 'webhook',
                        'error_category': 'external',
                        'severity': 'high',
                        'webhook_name': webhook_name
                    },
                    fingerprint=['WebhookHandler', webhook_name, 'webhook']
                )
                raise
        return wrapper
    return decorator