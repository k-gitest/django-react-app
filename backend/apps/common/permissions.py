from rest_framework import permissions
from .security import verify_qstash_signature


class IsQStashAuthenticated(permissions.BasePermission):
    """
    QStashからのリクエストのみを許可するカスタム権限
    
    署名検証に失敗した場合、403 Forbiddenを返す
    """
    
    def has_permission(self, request, view):
        return verify_qstash_signature(request)
    
    message = "Invalid QStash signature"