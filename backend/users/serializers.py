from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer as DefaultLoginSerializer
from rest_framework import serializers
from django.db import IntegrityError
from .models import CustomUser


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

    def validate_email(self, email):
        """
        メールアドレスの重複をチェック
        """
        if CustomUser.objects.filter(email__iexact=email).exists():
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
            'password1': self.validated_data.get('password1', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        }

    def save(self, request):
        """
        ユーザーを保存
        allauthのadapter経由でユーザーを作成
        """
        from allauth.account.adapter import get_adapter
        from allauth.account.utils import setup_user_email

        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        
        user.email = self.cleaned_data.get('email')
        user.set_password(self.cleaned_data.get('password1'))
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        
        try:
            user.save()
        except IntegrityError:
            raise serializers.ValidationError({
                'email': ['A user is already registered with this e-mail address.']
            })
        
        #setup_user_email(request, user, [])
        
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