from django.db import IntegrityError
from typing import Dict, Optional
from .models import CustomUser


# ============================================================================
# User Query Services (読み取り操作)
# ============================================================================
class UserQueryService:
    """
    ユーザー情報の取得に関するサービス
    """
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[CustomUser]:
        """
        メールアドレスでユーザーを取得
        
        Args:
            email: メールアドレス
            
        Returns:
            CustomUser or None
        """
        try:
            return CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            return None
    
    @staticmethod
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
    def get_user_by_id(user_id: int) -> Optional[CustomUser]:
        """
        IDでユーザーを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            CustomUser or None
        """
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None


# ============================================================================
# User Command Services (書き込み操作)
# ============================================================================
class UserCommandService:
    """
    ユーザー情報の作成・更新・削除に関するサービス
    """
    
    @staticmethod
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
            IntegrityError: メールアドレスが重複している場合
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
            IntegrityError: メールアドレスが重複している場合
        """
        from allauth.account.adapter import get_adapter
        
        adapter = get_adapter()
        user = adapter.new_user(request)
        
        user.email = email
        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        
        try:
            user.save()
        except IntegrityError as e:
            raise IntegrityError(f"User with email {email} already exists") from e
        
        return user
    
    @staticmethod
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
            ValueError: メールアドレスが既に登録されている場合
            IntegrityError: データベース制約エラー
        """
        email = user_data.get('email')
        
        # メールアドレスの重複チェック
        if self.query_service.email_exists(email):
            raise ValueError(f"A user is already registered with this e-mail address: {email}")
        
        # ユーザー作成
        user = self.command_service.create_user_with_adapter(
            request=request,
            email=email,
            password=user_data.get('password'),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )
        
        # 必要に応じてメール確認などの追加処理をここに追加
        # from allauth.account.utils import setup_user_email
        # setup_user_email(request, user, [])
        
        return user