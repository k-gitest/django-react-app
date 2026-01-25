from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer as DefaultLoginSerializer
from rest_framework import serializers

from .models import CustomUser
from .user_service import UserQueryService, UserRegistrationService


# ============================================================================
# 1. ユーザー情報表示・取得用のシリアライザー
# ============================================================================
class CustomUserSerializer(serializers.ModelSerializer):
    """
    現在のユーザー情報を返すシリアライザ
    
    読み取り専用フィールド:
        - id: ユーザーID
        - email: メールアドレス
        - is_staff: スタッフ権限
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
    
    - usernameフィールドを削除（emailを主キーとして使用）
    - first_name/last_nameフィールドを追加
    - サービス層経由でユーザー作成
    
    エラーハンドリング:
        - メールアドレス重複: UserAlreadyExistsError → 統一エラーハンドラーが処理
        - その他のエラー: 統一エラーハンドラーが処理
    """
    username = None
    
    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="ユーザーの名"
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        help_text="ユーザーの姓"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_service = UserQueryService()
        self.registration_service = UserRegistrationService()

    def get_cleaned_data(self):
        """
        登録時のクリーンデータを返す
        
        Returns:
            dict: バリデーション済みのユーザーデータ
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
        
        サービス層経由でユーザーを作成。
        エラーは統一エラーハンドラーが処理するため、try-catchは不要。
        
        Args:
            request: HTTPリクエストオブジェクト
        
        Returns:
            CustomUser: 作成されたユーザーインスタンス
        
        Raises:
            UserAlreadyExistsError: メールアドレス重複時（統一エラーハンドラーが処理）
            BaseAppError: その他のエラー（統一エラーハンドラーが処理）
        """
        cleaned_data = self.get_cleaned_data()
        
        # サービス層を呼び出すだけ（エラー処理は統一エラーハンドラーに委譲）
        user = self.registration_service.register_user(
            request=request,
            user_data=cleaned_data
        )
        
        return user


# ============================================================================
# 3. ログイン用のシリアライザー
# ============================================================================
class CustomLoginSerializer(DefaultLoginSerializer):
    """
    emailベース認証用のカスタムログインシリアライザ
    
    - usernameフィールドを削除
    - emailフィールドを使用
    """
    username = None
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'メールアドレスを入力してください。',
            'invalid': '有効なメールアドレスを入力してください。'
        }
    )


# ============================================================================
# 4. Webhook用シリアライザー
# ============================================================================
class WelcomeEmailWebhookSerializer(serializers.Serializer):
    """
    ウェルカムメール送信Webhookのペイロードバリデーション
    
    QStashから呼ばれるWebhook用のバリデーター
    """
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'email is required',
            'invalid': 'invalid email format'
        }
    )
    first_name = serializers.CharField(
        required=True,
        min_length=1,
        max_length=150,
        error_messages={
            'required': 'first_name is required',
            'blank': 'first_name cannot be blank'
        }
    )