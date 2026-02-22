"""
GraphQL User型定義
"""
import strawberry
import strawberry.django
from datetime import datetime
from typing import Optional
from typing import Union, Annotated

from apps.users.models import CustomUser
from apps.graphql_api.types.common import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    InternalError,
    Success,
)


# ============================================================================
# User型定義
# ============================================================================

@strawberry.django.type(CustomUser)
class UserType:
    """
    ユーザー型
    
    認証済みユーザー情報の表示用
    パスワード等の機密情報は含まない
    """
    id: int
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    date_joined: datetime
    
    # フルネーム（計算フィールド）
    @strawberry.field
    def full_name(self) -> str:
        """姓名を結合したフルネーム"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        return self.first_name or self.last_name or self.email


# ============================================================================
# 認証レスポンス型
# ============================================================================

@strawberry.type
class AuthPayload:
    """
    認証成功レスポンス（ログイン・登録共通）
    
    Note:
        - JWT CookieはHTTP Headerで自動送信されるため、
          GraphQLレスポンスには含めない
        - フロントエンドは user 情報のみを受け取る
    """
    user: UserType
    message: str = "認証に成功しました"
    
    __typename: str = "AuthPayload"


# ============================================================================
# Input型（Mutation用）
# ============================================================================

@strawberry.input
class RegisterInput:
    """
    ユーザー登録用Input型
    """
    email: str = strawberry.field(
        description="メールアドレス（ログインID）"
    )
    password: str = strawberry.field(
        description="パスワード（8文字以上）"
    )
    password_confirm: str = strawberry.field(
        description="パスワード確認"
    )
    first_name: Optional[str] = strawberry.field(
        default="",
        description="名"
    )
    last_name: Optional[str] = strawberry.field(
        default="",
        description="姓"
    )


@strawberry.input
class LoginInput:
    """
    ログイン用Input型
    """
    email: str = strawberry.field(
        description="メールアドレス"
    )
    password: str = strawberry.field(
        description="パスワード"
    )


@strawberry.input
class ChangePasswordInput:
    """
    パスワード変更用Input型
    """
    old_password: str = strawberry.field(
        description="現在のパスワード"
    )
    new_password: str = strawberry.field(
        description="新しいパスワード"
    )
    new_password_confirm: str = strawberry.field(
        description="新しいパスワード（確認）"
    )


# ============================================================================
# Result Union型
# ============================================================================

# 認証結果（ログイン・登録）
AuthResult = Annotated[
    Union[
        AuthPayload,
        ValidationError,
        ConflictError,
        RateLimitError,
        ExternalServiceError,
        InternalError,
    ],
    strawberry.union("AuthResult")
]

# ログアウト結果
LogoutResult = Annotated[
    Union[
        Success, AuthenticationError, InternalError,
    ],
    strawberry.union("LogoutResult")
]

# パスワード変更結果
ChangePasswordResult = Annotated[
    Union[
        Success, ValidationError, AuthenticationError, InternalError,
    ],
    strawberry.union("ChangePasswordResult")
]