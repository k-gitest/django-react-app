from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from apps.common.rest_schemas import CommonSchemas
from .serializers import TodoSerializer

class TodoSchemas:
    """Todo関連のOpenAPIスキーマ定義"""
    
    list = extend_schema(
        summary="Todoリスト取得",
        description="ログインユーザーに紐づくTodoアイテムの一覧を取得します。",
        responses={
            200: TodoSerializer(many=True),
            401: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        examples=[
            OpenApiExample(
                'Unauthorized',
                value={
                    'error': 'authentication_failed',
                    'detail': '認証情報が提供されていません。'
                },
                response_only=True,
                status_codes=['401'],
            ),
        ],
        tags=['Todos']
    )
    
    create = extend_schema(
        summary="Todo作成",
        description="""
        新しいTodoアイテムを作成します。
        
        作成後、非同期でベクトルインデックスに追加されます（QStash経由）。
        """,
        request=TodoSerializer,
        responses={
            201: TodoSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        examples=[
            OpenApiExample(
                'Validation Error',
                value={
                    'error': 'validation_error',
                    'detail': 'リクエストデータが不正です',
                },
                response_only=True,
                status_codes=['400'],
            ),
        ],
        tags=['Todos']
    )
    
    retrieve = extend_schema(
        summary="Todo詳細取得",
        description="指定されたIDのTodoアイテムの詳細を取得します。",
        responses={
            200: TodoSerializer,  # ✅ Serializerはそのまま使える
            401: {  # ✅ 型定義に変更
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
            404: {  # ✅ 型定義に変更
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        tags=['Todos']
    )
    
    update = extend_schema(
        summary="Todo更新（全体）",
        description="""
        指定されたIDのTodoアイテムを更新します。
        
        更新後、非同期でベクトルインデックスが更新されます（QStash経由）。
        """,
        request=TodoSerializer,
        responses={
            200: TodoSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        tags=['Todos']
    )
    
    partial_update = extend_schema(
        summary="Todo更新（部分）",
        description="""
        指定されたIDのTodoアイテムの一部を更新します。
        
        更新後、非同期でベクトルインデックスが更新されます（QStash経由）。
        """,
        request=TodoSerializer,
        responses={
            200: TodoSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        tags=['Todos']
    )
    
    destroy = extend_schema(
        summary="Todo削除",
        description="""
        指定されたIDのTodoアイテムを削除します。
        
        削除後、非同期でベクトルインデックスからも削除されます（QStash経由）。
        """,
        responses={
            204: None,  # ✅ 204はNone
            404: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        tags=['Todos']
    )
    
    stats = extend_schema(
        summary="優先度別統計",
        description="優先度ごとのTodo件数を取得します。Redisキャッシュを使用（15分間）。",
        responses={
            200: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'priority': {'type': 'string'},
                        'count': {'type': 'integer'},
                    }
                }
            },
        },
        tags=['Todos', 'Statistics']
    )
    
    progress_stats = extend_schema(
        summary="進捗分布統計",
        description="進捗率の分布を20%刻みで取得します。Redisキャッシュを使用（15分間）。",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'range_0_20': {'type': 'integer'},
                    'range_21_40': {'type': 'integer'},
                    'range_41_60': {'type': 'integer'},
                    'range_61_80': {'type': 'integer'},
                    'range_81_100': {'type': 'integer'},
                }
            },
        },
        tags=['Todos', 'Statistics']
    )
    
    search = extend_schema(
        summary="セマンティック検索",
        description="""
        自然言語でTodoを検索します。
        
        Google Gemini APIによるベクトル検索を使用し、
        「明日の会議関連」などの曖昧な検索が可能です。
        """,
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='検索クエリ（例: "明日の会議関連"）'
            ),
            OpenApiParameter(
                name='top_k',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='取得件数（デフォルト: 5、最大: 20）'
            ),
            OpenApiParameter(
                name='min_score',
                type=float,
                location=OpenApiParameter.QUERY,
                required=False,
                description='最小類似度スコア（デフォルト: 0.5、範囲: 0.0-1.0）'
            ),
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'score': {'type': 'number'},
                                'todo_title': {'type': 'string'},
                            }
                        }
                    },
                    'count': {'type': 'integer'},
                }
            },
        },
        examples=[
            OpenApiExample(
                'Success',
                value={
                    'query': '明日の会議',
                    'results': [
                        {'id': 1, 'score': 0.95, 'todo_title': '会議資料作成'}
                    ],
                    'count': 1
                },
                response_only=True,
                status_codes=['200'],
            ),
        ],
        tags=['Todos', 'Search']
    )
    
    bulk_index = extend_schema(
        summary="一括ベクトルインデックス",
        description="""
        既存のTodoをベクトルインデックスに一括追加します。
        
        非同期処理（QStash経由）でバックグラウンド実行されます。
        初期データ投入やリインデックス時に使用。
        """,
        request=None,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'status': {'type': 'string'},
                }
            },
            401: {  # ✅ 型定義に変更
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                }
            },
        },
        tags=['Todos', 'Indexing']
    )