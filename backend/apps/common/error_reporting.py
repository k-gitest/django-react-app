"""
エラー報告・モニタリング統合
現在の実装: Sentry
"""
import logging
from typing import Optional, Dict, Any, Union, Type, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from django.conf import settings

logger = logging.getLogger(__name__)


def _before_send(event: Dict, hint: Dict) -> Optional[Dict]:
    """Sentry送信前の前処理 (内部関数)"""
    if getattr(settings, 'TESTING', False):
        return None
    
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if exc_type.__name__ in ('Http404', 'Ratelimited'):
            return None
    
    if 'request' in event and 'data' in event['request']:
        for key in ['password', 'password1', 'password2', 'token']:
            if key in event['request']['data']:
                event['request']['data'][key] = '***REDACTED***'
    
    return event

def _apply_scope_data(
    scope: sentry_sdk.Scope,
    level: str,
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    user_info: Optional[Dict[str, Any]] = None,
    fingerprint: Optional[list] = None
):
    """スコープに対して共通のメタデータを一括設定する"""
    scope.level = level
    
    if extra:
        for key, value in extra.items():
            scope.set_extra(key, value)
    
    if tags:
        for key, value in tags.items():
            scope.set_tag(key, value)
            
    if user_info:
        scope.set_user(user_info)

    if fingerprint:
        scope.fingerprint = fingerprint


def _capture_exception_internal(
    exception: Exception,
    level: str = 'error',
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    user_info: Optional[Dict[str, Any]] = None,
    fingerprint: Optional[list] = None
):
    """内部実装: Sentryへ例外を送信"""
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        
        if user_info:
            scope.set_user(user_info)

        if fingerprint:
            scope.fingerprint = fingerprint
        
        capture_exception(exception)
    """
    with sentry_sdk.push_scope() as scope:
        _apply_scope_data(scope, level, **kwargs)
        sentry_sdk.capture_exception(exception)
    """


def _capture_message_internal(
    message: str,
    level: str = 'info',
    extra: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    fingerprint: Optional[list] = None
):
    """内部実装: Sentryへメッセージを送信"""
    with sentry_sdk.push_scope() as scope:
        scope.level = level
        
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        if fingerprint:
            scope.fingerprint = fingerprint
        
        capture_message(message)
    """
    with sentry_sdk.push_scope() as scope:
        _apply_scope_data(scope, level, **kwargs)
        sentry_sdk.capture_message(message)
    """

@dataclass
class ErrorProfile:
    """エラー報告のプロファイル（プリセット）"""
    error_category: str
    severity: str
    user_impact: str
    business_critical: str
    use_fingerprint: bool = False


class ErrorProfiles:
    """
    よく使うエラープロファイルのプリセット
    """
    # インフラ系（QStash, Email等）
    INFRASTRUCTURE_MEDIUM = ErrorProfile(
        error_category='infrastructure',
        severity='medium',
        user_impact='low',
        business_critical='false',
        use_fingerprint=True  # インフラエラーはグループ化
    )
    
    INFRASTRUCTURE_HIGH = ErrorProfile(
        error_category='infrastructure',
        severity='high',
        user_impact='medium',
        business_critical='false',
        use_fingerprint=True  # インフラエラーはグループ化
    )
    
    # 監視系（Analytics等）
    MONITORING_LOW = ErrorProfile(
        error_category='monitoring',
        severity='low',
        user_impact='none',
        business_critical='false',
        use_fingerprint=True  # 監視エラーはグループ化
    )
    
    # 外部サービス
    EXTERNAL_SERVICE_HIGH = ErrorProfile(
        error_category='external_service',
        severity='high',
        user_impact='high',
        business_critical='true',
        use_fingerprint=False
    )


class ErrorMonitor:
    """
    エラーモニタリング統合
    
    外部モニタリングサービスへのエラー報告を抽象化。
    実装の切り替えはこのクラス内部で行う。
    """

    @staticmethod
    def log_error(
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        user=None,
        fingerprint: Optional[list] = None
    ):
        """
        エラーをモニタリングサービスに報告
        
        Args:
            exception: 例外オブジェクト
            context: 追加コンテキスト情報 (Sentryのextra)
            tags: タグ情報 (Sentryでのフィルタリング・検索用)
            user: Userオブジェクト (任意)
            
        Example:
            ErrorMonitor.log_error(
                exception=e,
                context={
                    'user_id': user.id,
                    'service': 'UserAuthService',
                    'operation': 'register_user',
                },
                tags={
                    'component': 'qstash',
                    'severity': 'medium',
                    'user_impact': 'low',
                },
                user=user
            )
        """
        user_info = None
        if user and hasattr(user, 'id'):
            user_info = {
                'id': user.id,
                'email': getattr(user, 'email', None),
            }
        
        _capture_exception_internal(
            exception=exception,
            level='error',
            extra=context,
            tags=tags,
            user_info=user_info,
            fingerprint=fingerprint
        )
    
    @staticmethod
    def log_warning(
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        fingerprint: Optional[list] = None
    ):
        """
        警告をモニタリングサービスに報告
        
        Args:
            message: 警告メッセージ
            context: 追加コンテキスト情報
            tags: タグ情報
        """
        _capture_message_internal(
            message=message,
            level='warning',
            extra=context,
            tags=tags,
            fingerprint=fingerprint
        )
    
    @staticmethod
    def log_info(
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        fingerprint: Optional[list] = None
    ):
        """
        情報をモニタリングサービスに報告
        
        Args:
            message: 情報メッセージ
            context: 追加コンテキスト情報
            tags: タグ情報
        """
        _capture_message_internal(
            message=message,
            level='info',
            extra=context,
            tags=tags,
            fingerprint=fingerprint
        )

    @staticmethod
    @contextmanager
    def capture_and_continue(
        component: str,
        operation: str,
        service: str,
        expected_errors: Union[Type[Exception], Tuple[Type[Exception], ...]] = (),
        user=None,
        context: Optional[Dict[str, Any]] = None,
        profile: Optional[ErrorProfile] = None,
        # 個別指定用（profileより優先）
        error_category: Optional[str] = None,
        severity: Optional[str] = None,
        user_impact: Optional[str] = None,
        business_critical: Optional[str] = None,
        use_fingerprint: Optional[bool] = None
    ):
        """
        特定の処理ブロックで例外が発生しても、報告だけして続行する
        
        Args:
            component: コンポーネント名 ('qstash', 'analytics', 'email')
            operation: 操作名 ('send_welcome_email', 'log_auth_event')
            service: サービス名 ('UserRegistrationService')
            expected_errors: 期待されるエラー（単一のクラスまたはタプル）
            user: Userオブジェクト
            context: 追加のコンテキスト情報
            profile: エラープロファイル（プリセット）
            error_category: エラーカテゴリ（個別指定）
            severity: 重要度（個別指定）
            user_impact: ユーザー影響度（個別指定）
            business_critical: ビジネスクリティカル（個別指定）
            use_fingerprint: Fingerprintを使ってグループ化するか
            
        Examples:
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
        """
        # 入力バリデーションと正規化
        if expected_errors:
            # 単一の例外クラス (type) が渡された場合、タプルに変換
            if isinstance(expected_errors, type) and issubclass(expected_errors, Exception):
                normalized_errors = (expected_errors,)
            # 既にタプルの場合
            elif isinstance(expected_errors, tuple):
                normalized_errors = expected_errors
            else:
                # 不正な型が渡された場合
                logger.warning(
                    f"Invalid expected_errors type: {type(expected_errors)}. "
                    f"Expected Exception class or tuple of Exception classes. "
                    f"Using empty tuple instead."
                )
                normalized_errors = ()
        else:
            normalized_errors = ()
        
        # プロファイルからデフォルト値を取得
        if profile:
            _error_category = error_category or profile.error_category
            _severity = severity or profile.severity
            _user_impact = user_impact or profile.user_impact
            _business_critical = business_critical or profile.business_critical
            _use_fingerprint = use_fingerprint if use_fingerprint is not None else profile.use_fingerprint
        else:
            _error_category = error_category or 'infrastructure'
            _severity = severity or 'medium'
            _user_impact = user_impact or 'low'
            _business_critical = business_critical or 'false'
            _use_fingerprint = use_fingerprint if use_fingerprint is not None else False

        # Fingerprint の生成
        fingerprint = None
        if _use_fingerprint:
            fingerprint = [service, operation, component]
        
        try:
            yield
        except normalized_errors as e:  # 正規化したタプルを使用
            # 期待されるエラー: warning レベル
            logger.warning(
                f"Expected error in {component}.{operation}: {e}",
                extra={
                    'user_id': getattr(user, 'id', None),
                    'component': component,
                    'operation': operation,
                }
            )
            
            full_context = {
                'service': service,
                'operation': operation,
                'step': operation,
                **(context or {})
            }
            
            tags = {
                'component': component,
                'error_category': _error_category,
                'severity': _severity,
                'user_impact': _user_impact,
                'business_critical': _business_critical,
                'captured_via': 'capture_and_continue',
            }
            
            ErrorMonitor.log_error(
                exception=e,
                context=full_context,
                tags=tags,
                user=user,
                fingerprint=fingerprint
            )
            
        except Exception as e:
            # 予期しないエラー: error レベル + 高い重要度
            logger.error(
                f"Unexpected error in {component}.{operation}: {e}",
                extra={
                    'user_id': getattr(user, 'id', None),
                    'component': component,
                    'operation': operation,
                },
                exc_info=False
            )
            
            full_context = {
                'service': service,
                'operation': operation,
                'step': operation,
                **(context or {})
            }
            
            tags = {
                'component': component,
                'error_category': 'unexpected',
                'severity': 'high',
                'user_impact': _user_impact,
                'business_critical': _business_critical,
                'captured_via': 'capture_and_continue',
            }
            
            ErrorMonitor.log_error(
                exception=e,
                context=full_context,
                tags=tags,
                user=user,
                fingerprint=None # 予期しないエラーはグループ化しない
            )


# 後方互換性のためのエイリアス (移行期間用、将来削除予定)
capture_exception_with_context = _capture_exception_internal
capture_message_with_context = _capture_message_internal
before_send_sentry = _before_send