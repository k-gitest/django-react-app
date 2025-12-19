from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    カスタムユーザーモデルのためのマネージャー
    
    【なぜ必要？】
    - デフォルトのUserManagerは username を必須とするため、
      email ベースの認証では使用できない
    - createsuperuser コマンドが正常に動作するためには、
      create_user と create_superuser を email ベースで実装する必要がある
    - is_superuser や is_staff フィールドが正しくマイグレーションに
      含まれるようにするため
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """通常のユーザーを作成"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """スーパーユーザーを作成"""
        # スーパーユーザーはスタッフ権限とスーパーユーザー権限が必須
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        """
        【重要】ログイン時のメールアドレス大文字小文字問題を解決
        
        問題: ユーザーが User@Example.com で登録し、user@example.com で
        ログインしようとすると失敗する（ドメイン部分の大文字小文字が違うため）
        
        解決: ログイン時にもメールアドレスを正規化してから検索
        """
        case_insensitive_username_field = f'{self.model.USERNAME_FIELD}__iexact'
        return self.get(**{case_insensitive_username_field: username})


class CustomUser(AbstractUser):
    """
    メールアドレスベースの認証を使用するカスタムユーザーモデル
    
    【AbstractUser を選んだ理由】
    - is_staff, is_superuser, is_active, date_joined 等の
      便利なフィールドが既に用意されている
    - Django Admin のパーミッション機能がそのまま使える
    - グループやパーミッションの多対多リレーションも継承される
    
    【AbstractBaseUser との違い】
    - AbstractBaseUser: 最小限のフィールドのみ。全て自分で実装が必要
    - AbstractUser: フル機能。username を email に置き換えるだけで済む
    """
    
    # username フィールドを無効化
    # （これにより、DBに username カラムは作成されない）
    username = None
    
    # email を必須かつユニークに設定（ログインIDとして使用）
    email = models.EmailField(
        _("email address"),
        unique=True,
    )
    
    # ログインに使用するフィールドを 'email' に指定
    # authenticate() 関数がユーザー検索時に使用するフィールド
    USERNAME_FIELD = 'email'
    
    # createsuperuser コマンドで対話的に入力が求められる追加フィールド
    # （email と password は自動で求められるため、ここでは空リスト）
    REQUIRED_FIELDS = []
    
    # ★重要: マネージャーを CustomUserManager に設定 ★
    # これがないと User.objects.create_user() や createsuperuser が動作しない
    objects = CustomUserManager()
    
    class Meta:
        db_table = 'custom_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email