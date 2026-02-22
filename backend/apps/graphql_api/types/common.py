"""
GraphQLエラー型定義
既存のBaseAppError階層をGraphQL型に変換
"""
import strawberry
from typing import Optional, List
from enum import Enum
from typing import Union, Annotated


# ============================================================================
# エラーカテゴリEnum
# ============================================================================

@strawberry.enum
class ErrorCategory(Enum):
    """エラーカテゴリ（既存のBaseAppErrorと対応）"""
    VALIDATION = "validation"              # バリデーションエラー
    AUTHENTICATION = "authentication"      # 認証エラー
    AUTHORIZATION = "authorization"        # 認可エラー
    NOT_FOUND = "not_found"               # リソース不在
    CONFLICT = "conflict"                  # リソース競合
    RATE_LIMIT = "rate_limit"             # レート制限
    EXTERNAL_SERVICE = "external_service"  # 外部サービスエラー
    INTERNAL = "internal"                  # 内部エラー


# ============================================================================
# エラー型定義（Union型で使用）
# ============================================================================

@strawberry.type
class ValidationError:
    """
    バリデーションエラー（400）
    DRFのValidationError、BaseAppErrorのValidationErrorに対応
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.VALIDATION
    )
    message: str
    field: Optional[str] = None
    code: str = "validation_error"
    
    # フロントエンドでの判定用
    __typename: str = "ValidationError"


@strawberry.type
class AuthenticationError:
    """
    認証エラー（401）
    未ログイン、トークン無効等
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.AUTHENTICATION
    )
    message: str
    code: str = "authentication_required"
    
    __typename: str = "AuthenticationError"


@strawberry.type
class AuthorizationError:
    """
    認可エラー（403）
    権限不足、他人のリソースへのアクセス等
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.AUTHORIZATION
    )
    message: str
    code: str = "authorization_failed"
    
    __typename: str = "AuthorizationError"


@strawberry.type
class NotFoundError:
    """
    リソース不在エラー（404）
    Django Http404、get_object_or_404等
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.NOT_FOUND
    )
    message: str
    resource_type: Optional[str] = None  # 例: "Todo", "User"
    resource_id: Optional[str] = None
    code: str = "not_found"
    
    __typename: str = "NotFoundError"


@strawberry.type
class ConflictError:
    """
    リソース競合エラー（409）
    UserAlreadyExistsError等
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.CONFLICT
    )
    message: str
    conflicting_field: Optional[str] = None  # 例: "email"
    code: str = "resource_conflict"
    
    __typename: str = "ConflictError"


@strawberry.type
class RateLimitError:
    """
    レート制限エラー（429）
    django-ratelimitのRatelimited
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.RATE_LIMIT
    )
    message: str
    retry_after: Optional[int] = None  # 秒数
    code: str = "rate_limit_exceeded"
    
    __typename: str = "RateLimitError"


@strawberry.type
class ExternalServiceError:
    """
    外部サービスエラー（503）
    QStashError, AnalyticsError, VectorError, EmbeddingError等
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.EXTERNAL_SERVICE
    )
    message: str
    service_name: Optional[str] = None  # 例: "QStash", "Gemini API"
    code: str = "external_service_error"
    
    __typename: str = "ExternalServiceError"


@strawberry.type
class InternalError:
    """
    内部エラー（500）
    予期しない例外、IntegrityError等
    """
    category: ErrorCategory = strawberry.field(
        default=ErrorCategory.INTERNAL
    )
    message: str = "サーバー内部で予期しないエラーが発生しました"
    code: str = "internal_server_error"
    
    # 本番環境では詳細を隠す
    debug_info: Optional[str] = None
    
    __typename: str = "InternalError"


# ============================================================================
# 成功レスポンス
# ============================================================================

@strawberry.type
class Success:
    """汎用成功レスポンス"""
    message: str
    success: bool = True
    
    __typename: str = "Success"


# ============================================================================
# Union型定義（Result Pattern）
# ============================================================================

# すべてのエラー型をまとめたUnion
BaseError = Annotated[
    Union[
        ValidationError,
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        ConflictError,
        RateLimitError,
        ExternalServiceError,
        InternalError,
    ],
    strawberry.union("BaseError")
]

# Mutation結果の標準パターン
def create_result_union(success_type, name: Optional[str] = None):
    """
    Result Pattern用のUnion型を動的生成
    
    使用例:
        TodoResult = create_result_union(TodoType, "TodoResult")
    """
    union_name = name or f"{success_type.__name__}Result"
    
    return Annotated[
        Union[
            success_type,
            ValidationError,
            AuthenticationError,
            AuthorizationError,
            NotFoundError,
            ConflictError,
            RateLimitError,
            ExternalServiceError,
            InternalError,
        ],
        strawberry.union(union_name)
    ]