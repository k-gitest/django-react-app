import strawberry
from strawberry import relay
from typing import Union
from typing import Union, Annotated

from apps.todos.service import TodoCommandService
from apps.common.exceptions import BaseAppError
from apps.graphql_api.types.todo import (
    TodoType,
    TodoEdge,
    TodoCreateInput,
    TodoUpdateInput,
    CreateTodoPayload,
    UpdateTodoPayload,
    DeleteTodoPayload,
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

# ============================================================================
# Create専用
# ============================================================================
TodoCreateResult = Annotated[
    Union[
        CreateTodoPayload,      # 成功時: Edgeを返す
        ValidationError,        # 入力不備
        AuthenticationError,    # 未ログイン
        InternalError,          # サーバーエラー
    ],
    strawberry.union("TodoCreateResult")
]

# ============================================================================
# Update専用
# ============================================================================
TodoUpdateResult = Annotated[
    Union[
        UpdateTodoPayload,      # 成功時: Nodeを返す
        ValidationError,        # 入力不備
        NotFoundError,          # 指定IDが存在しない
        AuthenticationError,    # 未ログイン
        AuthorizationError,     # 他人のTodoを編集しようとした
        InternalError,
    ],
    strawberry.union("TodoUpdateResult")
]

# ============================================================================
# Delete専用
# ============================================================================
TodoDeleteResult = Annotated[
    Union[
        DeleteTodoPayload,      # 成功時: 削除されたIDを返す
        NotFoundError,          # 指定IDが存在しない
        AuthenticationError,
        AuthorizationError,
        InternalError,
    ],
    strawberry.union("TodoDeleteResult")
]

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
    ) -> TodoCreateResult:
        """
        Todo作成
        
        Returns:
            TodoCreateResult = CreateTodoPayload | ValidationError | ... | InternalError
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
        # return todo
        # ✅ Edgeを作って Payload で包んで返す
        return CreateTodoPayload(
            todo_edge=TodoEdge(
                node=todo,
                cursor=relay.to_base64("TodoType", todo.id)
            )
        )
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def update_todo(
        self,
        info: strawberry.Info,
        id: relay.GlobalID,
        input: TodoUpdateInput
    ) -> TodoUpdateResult:
        """
        Todo更新
        
        Returns:
            TodoUpdateResult = UpdateTodoPayload | ValidationError | ... | InternalError
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
        # return todo
        # Payloadで包んで返す
        return UpdateTodoPayload(todo=todo)
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def delete_todo(
        self,
        info: strawberry.Info,
        id: relay.GlobalID
    ) -> TodoDeleteResult:
        """
        Todo削除
        
        Returns:
            TodoDeleteResult = DeleteTodoPayload | NotFoundError | ... | InternalError
        """
        user = info.context.request.user
        db_id = id.node_id
        
        # Service層を呼び出し
        TodoCommandService.delete_todo(db_id, user)
        
        # return Success(message="Todoを削除しました")
        # ✅ 渡された GlobalID をそのまま「消えたID」として返してあげる
        return DeleteTodoPayload(
            deleted_todo_id=id, 
            message="Todoを削除しました"
        )
    
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