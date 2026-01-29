from typing import Any
from strawberry.permission import BasePermission
from strawberry.types import Info
import strawberry


class IsAuthenticated(BasePermission):
    """
    認証済みユーザーのみアクセス可能
    DRFのIsAuthenticatedに相当
    """
    message = "認証が必要です。ログインしてください。"
    
    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        request = info.context.request
        is_authenticated = request.user and request.user.is_authenticated
        
        if not is_authenticated:
            # ✅ ログに記録（監視用）
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Unauthenticated GraphQL access attempt: {info.field_name}")
        
        return is_authenticated


class IsOwner(BasePermission):
    """
    リソースのオーナーのみアクセス可能
    （将来的に実装、現状はService層で認可チェック）
    """
    message = "このリソースへのアクセス権限がありません。"
    
    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        # ✅ Service層で認可チェックしているため、現状は常にTrue
        # 将来的にはここでもチェック可能
        return True