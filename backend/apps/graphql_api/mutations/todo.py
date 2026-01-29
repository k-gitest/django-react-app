import strawberry
from strawberry import relay
from typing import Union

from apps.todos.service import TodoCommandService
from apps.common.exceptions import BaseAppError
from apps.graphql_api.types.todo import (
    TodoType,
    TodoCreateInput,
    TodoUpdateInput,
)
from apps.graphql_api.types.common import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
    InternalError,
    Success,
)
from apps.graphql_api.permissions import IsAuthenticated
from apps.graphql_api.validators import TodoValidator
from apps.graphql_api.errors.handlers import graphql_error_handler


# ============================================================================
# Result Union型の定義
# ============================================================================

TodoResult = strawberry.union(
    "TodoResult",
    types=(
        TodoType,
        ValidationError,
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        ConflictError,
        ExternalServiceError,
        InternalError,
    )
)

DeleteResult = strawberry.union(
    "DeleteResult",
    types=(
        Success,
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        ExternalServiceError,
        InternalError,
    )
)


# ============================================================================
# Mutation定義
# ============================================================================

@strawberry.type
class TodoMutation:
    """
    Todo関連のMutation定義
    
    エラーハンドリング:
    - @graphql_error_handler で統一的に処理
    - Result Patternで成功/失敗を明示
    - ErrorMonitorとの統合
    """
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def create_todo(
        self,
        info: strawberry.Info,
        input: TodoCreateInput
    ) -> TodoResult:
        """
        Todo作成
        
        Returns:
            TodoResult = TodoType | ValidationError | ... | InternalError
        """
        user = info.context.request.user
        
        # バリデーション（Strawberry層）
        validation_errors = TodoValidator.validate_create(input)
        if validation_errors:
            return validation_errors[0]
        
        # Service層を呼び出し
        # エラーは @graphql_error_handler が自動処理
        data = {
            "todo_title": input.todo_title,
            "priority": input.priority.value,
            "progress": input.progress,
        }
        
        todo = TodoCommandService.create_todo(user, data)
        return todo
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def update_todo(
        self,
        info: strawberry.Info,
        id: relay.GlobalID,
        input: TodoUpdateInput
    ) -> TodoResult:
        """
        Todo更新
        
        Returns:
            TodoResult = TodoType | ValidationError | ... | InternalError
        """
        user = info.context.request.user
        db_id = id.node_id
        
        # バリデーション
        validation_errors = TodoValidator.validate_update(input)
        if validation_errors:
            return validation_errors[0]
        
        # Service層を呼び出し
        data = {}
        if input.todo_title is not None:
            data["todo_title"] = input.todo_title
        if input.priority is not None:
            data["priority"] = input.priority.value
        if input.progress is not None:
            data["progress"] = input.progress
        
        todo = TodoCommandService.update_todo(db_id, user, data)
        return todo
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def delete_todo(
        self,
        info: strawberry.Info,
        id: relay.GlobalID
    ) -> DeleteResult:
        """
        Todo削除
        
        Returns:
            DeleteResult = Success | AuthenticationError | ... | InternalError
        """
        user = info.context.request.user
        db_id = id.node_id
        
        # Service層を呼び出し
        TodoCommandService.delete_todo(db_id, user)
        
        return Success(message="Todoを削除しました")
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def bulk_index_todos(
        self,
        info: strawberry.Info
    ) -> Union[Success, ExternalServiceError, InternalError]:
        """
        全Todoをベクトルインデックスに一括登録（非同期）
        
        Returns:
            Success | ExternalServiceError | InternalError
        """
        user = info.context.request.user
        
        from apps.todos.service import TodoSearchService
        TodoSearchService.bulk_index_todos(user)
        
        return Success(message="インデックス処理をバックグラウンドで開始しました")