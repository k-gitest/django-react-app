import strawberry
from strawberry import relay
from typing import Optional
from datetime import datetime

from apps.todos.models import Todo


# ============================================================================
# Enum定義（Strawberryではenumを明示的に定義）
# ============================================================================

@strawberry.enum
class PriorityEnum:
    """優先度Enum（モデルのCHOICESと同期）"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ============================================================================
# 型定義 (Types) - DRFのSerializerに相当
# ============================================================================

@strawberry.django.type(Todo)
class TodoType(relay.Node):
    """
    TodoモデルをGraphQL型に変換。
    relay.Nodeを継承することで、フロント側でIDが自動的にGlobal ID(Base64)化され
    キャッシュ管理が容易になります。
    """
    id: relay.GlobalID
    todo_title: str
    priority: PriorityEnum  # ✅ enumに変更
    progress: int
    created_at: datetime  # ✅ strawberry.datetime → datetime
    updated_at: datetime
    
    # ✅ user情報も追加（リレーション対応、将来的にUserTypeに変更可能）
    user_email: str = strawberry.field(
        description="TodoのオーナーのEmailアドレス"
    )
    
    @staticmethod
    def resolve_user_email(root: Todo, info: strawberry.Info) -> str:
        """user.emailをresolve（N+1問題に注意、将来的にDataLoaderで最適化）"""
        return root.user.email


@strawberry.type
class PriorityStatsType:
    """優先度別統計用カスタム型"""
    priority: PriorityEnum  # ✅ enumに変更
    count: int


@strawberry.type
class ProgressStatsType:
    """進捗統計用カスタム型（REST APIの /progress-stats/ 相当）"""
    range_0_20: int
    range_21_40: int
    range_41_60: int
    range_61_80: int
    range_81_100: int


@strawberry.type
class SearchResultType:
    """ベクトル検索結果用カスタム型"""
    id: int
    todo_title: str
    priority: PriorityEnum  # ✅ enumに変更
    progress: int
    score: float  # 類似度スコア


# ============================================================================
# Input Types（Mutationの引数用）
# ============================================================================

@strawberry.input
class TodoCreateInput:
    """Todo作成用Input型（バリデーションルールを明示）"""
    todo_title: str = strawberry.field(
        description="タスクのタイトル（1-200文字）"
    )
    priority: PriorityEnum = strawberry.field(
        default=PriorityEnum.MEDIUM,
        description="優先度"
    )
    progress: int = strawberry.field(
        default=0,
        description="進捗率（0-100）"
    )


@strawberry.input
class TodoUpdateInput:
    """Todo更新用Input型（全てOptional）"""
    todo_title: Optional[str] = strawberry.field(
        default=None,
        description="タスクのタイトル（1-200文字）"
    )
    priority: Optional[PriorityEnum] = strawberry.field(
        default=None,
        description="優先度"
    )
    progress: Optional[int] = strawberry.field(
        default=None,
        description="進捗率（0-100）"
    )


@strawberry.input
class TodoSearchInput:
    """検索用Input型"""
    query: str = strawberry.field(
        description="検索クエリ（自然言語）"
    )
    top_k: int = strawberry.field(
        default=5,
        description="返す結果数（1-100）"
    )
    min_score: float = strawberry.field(
        default=0.5,
        description="最小類似度スコア（0.0-1.0）"
    )


# ============================================================================
# Relay Connection Types（ページネーション対応）
# ============================================================================

@strawberry.type
class TodoEdge(relay.Edge):
    """TodoのEdge（ページネーション用）"""
    node: TodoType


@strawberry.type
class TodoConnection(relay.Connection):
    """TodoのConnection（ページネーション用）"""
    edges: list[TodoEdge]
    page_info: relay.PageInfo
    
    # ✅ 統計情報も一緒に返せる（1回のクエリで取得可能）
    total_count: int = strawberry.field(
        description="ユーザーのTodo総数"
    )