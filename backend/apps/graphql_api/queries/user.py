"""
GraphQL User Query定義
"""
import strawberry
from typing import Optional

from apps.users.user_service import UserQueryService
from apps.graphql_api.types.user import UserType
from apps.graphql_api.types.common import AuthenticationError
from apps.graphql_api.permissions import IsAuthenticated
from apps.graphql_api.errors.handlers import graphql_error_handler


@strawberry.type
class UserQuery:
    """
    User関連のQuery定義
    """
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def me(self, info: strawberry.Info) -> Optional[UserType]:
        """
        現在のログインユーザー情報を取得
        
        Query例:
        {
          me {
            id
            email
            fullName
            isStaff
          }
        }
        
        Returns:
            UserType | None
        """
        user = info.context.request.user
        
        if not user or not user.is_authenticated:
            return None
        
        return user
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def user(self, info: strawberry.Info, id: int) -> Optional[UserType]:
        """
        特定のユーザー情報を取得（将来的な拡張用）
        
        Query例:
        {
          user(id: 1) {
            id
            email
            fullName
          }
        }
        
        Note:
            - 現状は自分自身のみ取得可能
            - 将来的に管理者権限でのユーザー管理機能を追加可能
        
        Returns:
            UserType | None
        """
        request_user = info.context.request.user
        
        # 本人のみ取得可能（将来的に管理者権限を追加）
        if request_user.id != id and not request_user.is_staff:
            return None
        
        return UserQueryService.get_user_by_id(id)