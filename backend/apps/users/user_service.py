from django.conf import settings
from django.db import transaction
from typing import Dict, Optional
import logging

from apps.common.error_decorators import service_error_handler
from apps.common.exceptions import UserAlreadyExistsError, AnalyticsError, QStashError

from .models import CustomUser
from .qstash_service import UserQStashService
from .analytics_service import AnalyticsService


logger = logging.getLogger(__name__)

# ============================================================================
# User Query Services (読み取り操作)
# ============================================================================
class UserQueryService:
    """
    ユーザー情報の取得に関するサービス
    """
    
    @staticmethod
    @service_error_handler
    def get_user_by_email(email: str) -> Optional[CustomUser]:
        """
        メールアドレスでユーザーを取得
        
        Args:
            email: メールアドレス
            
        Returns:
            CustomUser or None
        """
        """
        try:
            return CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            return None
        """

        return CustomUser.objects.filter(email__iexact=email).first()
    
    @staticmethod
    @service_error_handler
    def email_exists(email: str) -> bool:
        """
        メールアドレスが既に登録されているかチェック
        
        Args:
            email: チェックするメールアドレス
            
        Returns:
            True if exists, False otherwise
        """
        return CustomUser.objects.filter(email__iexact=email).exists()
    
    @staticmethod
    @service_error_handler
    def get_user_by_id(user_id: int) -> Optional[CustomUser]:
        """
        IDでユーザーを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            CustomUser or None
        """
        """
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None
        """

        return CustomUser.objects.filter(id=user_id).first()


# ============================================================================
# User Command Services (書き込み操作)
# ============================================================================
class UserCommandService:
    """
    ユーザー情報の作成・更新・削除に関するサービス
    """
    
    @staticmethod
    @service_error_handler
    def create_user(email: str, password: str, first_name: str = '', 
                   last_name: str = '', **extra_fields) -> CustomUser:
        """
        新規ユーザーを作成
        
        Args:
            email: メールアドレス
            password: パスワード（プレーンテキスト）
            first_name: 名
            last_name: 姓
            **extra_fields: その他のフィールド
            
        Returns:
            作成されたCustomUserインスタンス
            
        Raises:
            UserAlreadyExistsError: メールアドレス重複時（デコレーターが自動変換）
        """
        user = CustomUser(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user
    
    @staticmethod
    @service_error_handler
    def create_user_with_adapter(request, email: str, password: str,
                                first_name: str = '', last_name: str = '') -> CustomUser:
        """
        allauthのadapterを使用してユーザーを作成
        
        Args:
            request: HTTPリクエストオブジェクト
            email: メールアドレス
            password: パスワード（プレーンテキスト）
            first_name: 名
            last_name: 姓
            
        Returns:
            作成されたCustomUserインスタンス
            
        Raises:
            UserAlreadyExistsError: メールアドレス重複時（デコレーターが自動変換）
        """
        from allauth.account.adapter import get_adapter
        
        adapter = get_adapter()
        user = adapter.new_user(request)
        
        user.email = email
        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name

        user.save()
        return user
    
    @staticmethod
    @service_error_handler
    def update_user(user: CustomUser, **fields) -> CustomUser:
        """
        ユーザー情報を更新
        
        Args:
            user: 更新するCustomUserインスタンス
            **fields: 更新するフィールド
            
        Returns:
            更新されたCustomUserインスタンス
        """
        for field, value in fields.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()
        return user
    
    @staticmethod
    @service_error_handler
    def change_password(user: CustomUser, new_password: str) -> CustomUser:
        """
        ユーザーのパスワードを変更
        
        Args:
            user: CustomUserインスタンス
            new_password: 新しいパスワード（プレーンテキスト）
            
        Returns:
            更新されたCustomUserインスタンス
        """
        user.set_password(new_password)
        user.save()
        return user
    
    @staticmethod
    @service_error_handler
    def delete_user(user: CustomUser) -> None:
        """
        ユーザーを削除
        
        Args:
            user: 削除するCustomUserインスタンス
        """
        user.delete()


# ============================================================================
# User Registration Service (登録フロー全体を管理)
# ============================================================================
class UserRegistrationService:
    """
    ユーザー登録フロー全体を管理するサービス
    """
    
    def __init__(self):
        self.query_service = UserQueryService()
        self.command_service = UserCommandService()
    
    @service_error_handler
    @transaction.atomic
    def register_user(self, request, user_data: Dict) -> CustomUser:
        """
        ユーザー登録処理
        
        Args:
            request: HTTPリクエストオブジェクト
            user_data: ユーザー登録データ
                - email: メールアドレス
                - password: パスワード
                - first_name: 名（オプション）
                - last_name: 姓（オプション）
                
        Returns:
            作成されたCustomUserインスタンス
            
        Raises:
            UserAlreadyExistsError: メールアドレスが既に登録されている場合
            ValidationError: その他のバリデーションエラー
        """
        email = user_data.get('email')
        
        # メールアドレスの重複チェック
        if self.query_service.email_exists(email):
            raise UserAlreadyExistsError(email=email)
        
        # ユーザー作成
        user = self.command_service.create_user_with_adapter(
            request=request,
            email=email,
            password=user_data.get('password'),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )
        
        # 外部サービス（QStash, Analytics）はon_commitで実行
        # DB保存が完全に成功（コミット）した直後にだけ走るようにする

        # ウェルカムメール送信を予約タスクを登録
        if not getattr(settings, "TESTING", False):
            transaction.on_commit(lambda: self._send_welcome_email_safely(user))
            
            # 分析ログ記録を予約タスクを登録
            transaction.on_commit(lambda: self._log_registration_safely(user, request))
        
        return user

    @staticmethod
    def _send_welcome_email_safely(user: CustomUser):
        """ウェルカムメール送信を安全に実行（失敗してもエラーを投げない）"""
        try:
            UserQStashService.send_welcome_email_async(
                email=user.email,
                first_name=user.first_name or "User"
            )
        except QStashError as e:
            logger.warning(
                f"Failed to queue welcome email: {e.message}",
                extra={'user_id': user.id, 'email': user.email}
            )
        except Exception as e:
            logger.error(
                f"Unexpected error queuing welcome email: {e}",
                extra={'user_id': user.id}
            )
    
    @staticmethod
    def _log_registration_safely(user: CustomUser, request):
        """登録イベントログを安全に実行（失敗してもエラーを投げない）"""
        try:
            AnalyticsService.log_auth_event(
                user=user,
                event_type="register",
                request=request,
                success=True
            )
        except AnalyticsError as e:
            logger.warning(
                f"Failed to log registration event: {e.message}",
                extra={'user_id': user.id}
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in analytics: {e}",
                extra={'user_id': user.id}
            )

# ============================================================================
# User Auth Service (認証認可に関する管理)
# ============================================================================
class UserAuthService:
    """
    ログイン・ログアウト・セッション管理など、
    認証に伴うビジネスロジックを担当
    """

    @staticmethod
    def handle_login_success(user: CustomUser, request):
        """
        ログイン成功時に実行すべき副作用をまとめる
        """
        # 分析ログの記録（DBを使わないので transaction なしでも良いが、
        # サービスの整合性として settings.TESTING チェックは入れる）
        UserAuthService._log_analytics_safely(user, "login", request)

    @staticmethod
    def handle_logout(request):
        """ログアウト処理の副作用"""
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            UserAuthService._log_analytics_safely(user, "logout", request)

    @staticmethod
    def _log_analytics_safely(user: CustomUser, event_type: str, request):
        """
        分析ログ送信を安全に実行（失敗してもエラーを投げない）
        
        Args:
            user: ユーザーオブジェクト
            event_type: "login" | "logout"
            request: HTTPリクエスト
        """
        if getattr(settings, "TESTING", False):
            return

        try:
            AnalyticsService.log_auth_event(
                user=user,
                event_type=event_type,
                request=request,
                success=True
            )
        except AnalyticsError as e:
            logger.warning(
                f"Analytics logging failed: {e.message}",
                extra={
                    'event_type': event_type,
                    'user_id': getattr(user, 'id', None)
                }
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in analytics: {e}",
                extra={
                    'event_type': event_type,
                    'user_id': getattr(user, 'id', None)
                }
            )