from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer as DefaultLoginSerializer
from rest_framework import serializers
from django.db import IntegrityError

from .models import CustomUser
from .services import UserQueryService, UserRegistrationService


# ============================================================================
# 1. ユーザー情報表示・取得用のシリアライザー
# ============================================================================
class CustomUserSerializer(serializers.ModelSerializer):
    """
    現在のユーザー情報を返すシリアライザ
    """
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'is_staff')
        read_only_fields = ('id', 'email', 'is_staff')


# ============================================================================
# 2. ユーザー作成（サインアップ）用のシリアライザー
# ============================================================================
class CustomRegisterSerializer(RegisterSerializer):
    """
    emailベース認証用のカスタム登録シリアライザ
    usernameフィールドを削除し、first_name/last_nameを追加
    """
    username = None
    
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_service = UserQueryService()
        self.registration_service = UserRegistrationService()

    def validate_email(self, email):
        """
        メールアドレスの重複をチェック
        """
        if self.query_service.email_exists(email):
            raise serializers.ValidationError(
                "A user is already registered with this e-mail address."
            )
        return email

    def get_cleaned_data(self):
        """
        登録時のクリーンデータを返す
        """
        return {
            'email': self.validated_data.get('email', ''),
            'password': self.validated_data.get('password1', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        }

    def save(self, request):
        """
        ユーザーを保存
        サービス層経由でユーザーを作成
        """
        cleaned_data = self.get_cleaned_data()
        
        try:
            user = self.registration_service.register_user(
                request=request,
                user_data=cleaned_data
            )
        except ValueError as e:
            # サービス層からのバリデーションエラー
            raise serializers.ValidationError({
                'email': [str(e)]
            })
        except IntegrityError:
            # データベース制約エラー
            raise serializers.ValidationError({
                'email': ['A user is already registered with this e-mail address.']
            })
        
        return user


# ============================================================================
# 3. ログイン用のシリアライザー（オプション）
# ============================================================================
class CustomLoginSerializer(DefaultLoginSerializer):
    """
    emailベース認証用のカスタムログインシリアライザ
    """
    username = None
    email = serializers.EmailField(required=True)