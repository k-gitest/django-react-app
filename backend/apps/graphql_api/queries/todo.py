import strawberry
from strawberry import relay
from typing import List, Optional

from apps.todos.service import TodoQueryService, TodoStatsService, TodoSearchService
from apps.common.exceptions import BaseAppError
from ..types.todo import (
    TodoType,
    TodoConnection,
    PriorityStatsType,
    ProgressStatsType,
    SearchResultType,
    TodoSearchInput,
    TodoEdge,
)
from ..types.common import OperationError
from ..permissions import IsAuthenticated


# ============================================================================
# 取得系 (Query) - ViewSetの list, retrieve, search に相当
# ============================================================================

@strawberry.type
class TodoQuery:
    """
    Todo関連のQuery定義
    全てのQueryに @strawberry.field デコレータと permission_classes を付与
    """
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    def todos(self, info: strawberry.Info) -> List[TodoType]:
        """
        全Todo取得（シンプル版）
        
        Query例:
        {
          todos {
            id
            todoTitle
            priority
            progress
          }
        }
        """
        user = info.context.request.user
        return TodoQueryService.get_user_todos(user)
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    def todos_connection(
        self,
        info: strawberry.Info,
        first: Optional[int] = 10,
        after: Optional[str] = None,
    ) -> TodoConnection:
        """
        全Todo取得（Relay Pagination対応版）
        
        Query例:
        {
          todosConnection(first: 10, after: "cursor123") {
            edges {
              node {
                id
                todoTitle
              }
              cursor
            }
            pageInfo {
              hasNextPage
              endCursor
            }
            totalCount
          }
        }
        """
        user = info.context.request.user
        todos = TodoQueryService.get_user_todos(user)
        
        # ✅ 将来的にはDjangoのpaginationと統合
        # 現状は簡易実装
        total_count = todos.count()
        
        return TodoConnection(
            edges=[TodoEdge(node=todo) for todo in todos],
            page_info=relay.PageInfo(
                has_next_page=False,
                has_previous_page=False,
                start_cursor=None,
                end_cursor=None,
            ),
            total_count=total_count,
        )
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    def todo(
        self,
        info: strawberry.Info,
        id: relay.GlobalID
    ) -> Optional[TodoType]:
        """
        個別Todo取得
        
        Query例:
        {
          todo(id: "VG9kb1R5cGU6MQ==") {
            id
            todoTitle
            priority
          }
        }
        """
        user = info.context.request.user
        # ✅ RelayのGlobal IDを整数IDに変換
        db_id = id.node_id
        return TodoQueryService.get_todo_by_id(db_id, user)
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    def priority_stats(self, info: strawberry.Info) -> List[PriorityStatsType]:
        """
        優先度別統計
        
        Query例:
        {
          priorityStats {
            priority
            count
          }
        }
        """
        user = info.context.request.user
        stats_list = TodoStatsService.get_priority_stats(user)
        
        # ✅ Service層が返す辞書リストをTypeクラスに変換
        return [
            PriorityStatsType(
                priority=item["priority"],
                count=item["count"]
            )
            for item in stats_list
        ]
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    def progress_stats(self, info: strawberry.Info) -> ProgressStatsType:
        """
        進捗統計
        
        Query例:
        {
          progressStats {
            range_0_20
            range_21_40
            range_41_60
            range_61_80
            range_81_100
          }
        }
        """
        user = info.context.request.user
        stats = TodoStatsService.get_progress_stats(user)
        
        # ✅ 辞書をProgressStatsTypeに変換
        return ProgressStatsType(**stats)
    
    @strawberry.field(permission_classes=[IsAuthenticated])
    def search_todos(
        self,
        info: strawberry.Info,
        input: TodoSearchInput  # ✅ Input型を使用
    ) -> List[SearchResultType]:
        """
        セマンティック検索
        
        Query例:
        {
          searchTodos(input: {
            query: "明日の会議関連"
            topK: 5
            minScore: 0.5
          }) {
            id
            todoTitle
            score
          }
        }
        """
        user = info.context.request.user
        
        # ✅ Service層の例外は統一エラーハンドラーでキャッチ
        # （VectorError, EmbeddingError等）
        results = TodoSearchService.search_similar_todos(
            user,
            input.query,
            top_k=input.top_k,
            min_score=input.min_score
        )
        
        # ✅ Service層の返り値をSearchResultTypeに変換
        return [
            SearchResultType(
                id=item["id"],
                todo_title=item["title"],  # ✅ keyを確認（"title" or "todo_title"）
                priority=item["priority"],
                progress=item["progress"],
                score=item["score"],
            )
            for item in results
        ]