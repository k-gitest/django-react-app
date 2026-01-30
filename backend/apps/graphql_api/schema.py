import strawberry
from strawberry.extensions import QueryDepthLimiter

from apps.graphql_api.queries.todo import TodoQuery
from apps.graphql_api.queries.user import UserQuery
from apps.graphql_api.mutations.todo import TodoMutation
from apps.graphql_api.mutations.user import UserMutation


# ============================================================================
# ルートQuery（統合）
# ============================================================================

@strawberry.type
class Query(TodoQuery, UserQuery):
    """
    GraphQLのルートQuery
    
    各アプリのQueryを統合:
        - TodoQuery: Todo関連のクエリ
        - UserQuery: User関連のクエリ
    """
    pass


# ============================================================================
# ルートMutation（統合）
# ============================================================================

@strawberry.type
class Mutation(TodoMutation, UserMutation):
    """
    GraphQLのルートMutation
    
    各アプリのMutationを統合:
        - TodoMutation: Todo関連のミューテーション
        - UserMutation: User関連のミューテーション（認証含む）
    """
    pass


# ============================================================================
# Strawberryスキーマの作成
# ============================================================================

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    
    # セキュリティ設定
    extensions=[
        QueryDepthLimiter(max_depth=10),  # ネストの深さ制限
    ],
)