"""
Tests for todos services
すべてのサービス層のテストを網羅
"""

from unittest.mock import MagicMock, patch

from apps.todos.analytics_service import TodoAnalyticsService
from apps.todos.embedding_service import TodoEmbeddingService
from apps.todos.models import Todo
from apps.todos.qstash_service import TodoQStashService
from apps.todos.service import TodoCommandService, TodoQueryService, TodoStatsService
from apps.todos.vector_service import VectorService
from apps.todos.webhook_service import TodoWebhookService
from apps.common.services.base_analytics import BaseAnalyticsService
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import Http404
from django.test import TestCase, override_settings

User = get_user_model()


# ================================
# TodoQueryService Tests
# ================================


class TodoQueryServiceTestCase(TestCase):
    """TodoQueryService のテスト"""

    def setUp(self):
        """各テストの前に実行"""
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", password="pass123"
        )
        self.todo1 = Todo.objects.create(user=self.user1, todo_title="User1 Todo")
        self.todo2 = Todo.objects.create(user=self.user2, todo_title="User2 Todo")

    def test_get_user_todos(self):
        """ユーザーのTodo取得"""
        todos = TodoQueryService.get_user_todos(self.user1)

        self.assertEqual(todos.count(), 1)
        self.assertEqual(todos.first(), self.todo1)

    def test_get_user_todos_isolation(self):
        """ユーザーは自分のTodoのみ取得可能"""
        todos = TodoQueryService.get_user_todos(self.user1)

        self.assertNotIn(self.todo2, todos)

    def test_get_todo_by_id(self):
        """IDでTodo取得"""
        todo = TodoQueryService.get_todo_by_id(self.todo1.id, self.user1)

        self.assertEqual(todo, self.todo1)

    def test_get_todo_by_id_wrong_user(self):
        """間違ったユーザーではNoneを返す"""
        todo = TodoQueryService.get_todo_by_id(self.todo1.id, self.user2)

        self.assertIsNone(todo)

    def test_get_todo_or_404(self):
        """Todo取得または404"""
        todo = TodoQueryService.get_todo_or_404(self.todo1.id, self.user1)
        self.assertEqual(todo, self.todo1)

        with self.assertRaises(Http404):
            TodoQueryService.get_todo_or_404(self.todo1.id, self.user2)


# ================================
# TodoStatsService Tests
# ================================


class TodoStatsServiceTestCase(TestCase):
    """TodoStatsService のテスト"""

    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        cache.clear()

    def tearDown(self):
        """各テストの後に実行"""
        cache.clear()

    def test_get_priority_stats(self):
        """優先度統計の取得"""
        Todo.objects.create(
            user=self.user, todo_title="High1", priority=Todo.Priority.HIGH
        )
        Todo.objects.create(
            user=self.user, todo_title="High2", priority=Todo.Priority.HIGH
        )
        Todo.objects.create(
            user=self.user, todo_title="Low1", priority=Todo.Priority.LOW
        )

        stats = TodoStatsService.get_priority_stats(self.user)

        high_stat = next((s for s in stats if s["priority"] == "HIGH"), None)
        low_stat = next((s for s in stats if s["priority"] == "LOW"), None)

        self.assertEqual(high_stat["count"], 2)
        self.assertEqual(low_stat["count"], 1)

    def test_get_progress_stats(self):
        """進捗統計の取得"""
        Todo.objects.create(user=self.user, todo_title="T1", progress=10)
        Todo.objects.create(user=self.user, todo_title="T2", progress=30)
        Todo.objects.create(user=self.user, todo_title="T3", progress=90)

        stats = TodoStatsService.get_progress_stats(self.user)

        self.assertEqual(stats["range_0_20"], 1)
        self.assertEqual(stats["range_21_40"], 1)
        self.assertEqual(stats["range_81_100"], 1)

    def test_stats_caching(self):
        """統計がキャッシュされる"""
        Todo.objects.create(
            user=self.user, todo_title="Test", priority=Todo.Priority.HIGH
        )

        stats1 = TodoStatsService.get_priority_stats(self.user)
        Todo.objects.create(
            user=self.user, todo_title="Test2", priority=Todo.Priority.HIGH
        )
        stats2 = TodoStatsService.get_priority_stats(self.user)

        self.assertEqual(stats1, stats2)

    def test_invalidate_stats_cache(self):
        """キャッシュの無効化"""
        Todo.objects.create(user=self.user, todo_title="Test")

        TodoStatsService.get_priority_stats(self.user)
        TodoStatsService.get_progress_stats(self.user)

        TodoStatsService.invalidate_stats_cache(self.user.id)

        cache_key_priority = TodoStatsService._get_stats_cache_key(
            self.user.id, "priority"
        )
        cache_key_progress = TodoStatsService._get_stats_cache_key(
            self.user.id, "progress"
        )

        self.assertIsNone(cache.get(cache_key_priority))
        self.assertIsNone(cache.get(cache_key_progress))


# ================================
# TodoCommandService Tests
# ================================


class TodoCommandServiceTestCase(TestCase):
    """TodoCommandService のテスト"""

    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        cache.clear()

    def tearDown(self):
        """各テストの後に実行"""
        cache.clear()

    @override_settings(TESTING=True)
    def test_create_todo(self):
        """Todo作成"""
        data = {"todo_title": "New Todo", "priority": "HIGH", "progress": 0}

        todo = TodoCommandService.create_todo(self.user, data)

        self.assertEqual(todo.todo_title, "New Todo")
        self.assertEqual(todo.priority, "HIGH")
        self.assertEqual(todo.user, self.user)

    @override_settings(TESTING=True)
    def test_update_todo(self):
        """Todo更新"""
        todo = Todo.objects.create(user=self.user, todo_title="Original", progress=0)

        updated = TodoCommandService.update_todo(
            todo.id, self.user, {"todo_title": "Updated", "progress": 50}
        )

        self.assertEqual(updated.todo_title, "Updated")
        self.assertEqual(updated.progress, 50)

    @override_settings(TESTING=True)
    def test_update_todo_wrong_user(self):
        """間違ったユーザーでの更新は404"""
        other_user = User.objects.create_user(
            email="other@example.com", password="pass123"
        )
        todo = Todo.objects.create(user=self.user, todo_title="Test")

        with self.assertRaises(Http404):
            TodoCommandService.update_todo(
                todo.id, other_user, {"todo_title": "Hacked"}
            )

    @override_settings(TESTING=True)
    def test_delete_todo(self):
        """Todo削除"""
        todo = Todo.objects.create(user=self.user, todo_title="Delete Me")
        todo_id = todo.id

        TodoCommandService.delete_todo(todo_id, self.user)

        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    @override_settings(TESTING=True)
    def test_cache_invalidation_on_create(self):
        """作成時にキャッシュが無効化される"""
        TodoStatsService.get_priority_stats(self.user)

        TodoCommandService.create_todo(
            self.user, {"todo_title": "Test", "priority": "HIGH", "progress": 0}
        )

        cache_key = TodoStatsService._get_stats_cache_key(self.user.id, "priority")
        self.assertIsNone(cache.get(cache_key))


# ================================
# TodoAnalyticsService Tests
# ================================


class TodoAnalyticsServiceTestCase(TestCase):
    """TodoAnalyticsService のテスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の開始時に一度だけ実行"""
        super().setUpClass()
        # 他のテストケース（別アプリなど）が残したシングルトンの残骸を徹底的に掃除
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        from apps.common.services.base_analytics import BaseAnalyticsService
        
        # クラスレベルの変数をすべてリセット
        TodoAnalyticsService._client = None
        BaseAnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None
    
    def setUp(self):
        """各テストの前に実行"""
        # ここでもリセットをかける（念には念を）
        TodoAnalyticsService._client = None
        
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=50
        )
    
    def tearDown(self):
        """各テストの後に実行"""
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        TodoAnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None
    
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_todo_create(self, mock_setup_schema, mock_connect):
        """Todo作成イベントのログ"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = TodoAnalyticsService.log_todo_create(self.user, self.todo)
        
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()
    
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_todo_update(self, mock_setup_schema, mock_connect):
        """Todo更新イベントのログ"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        changed_fields = {"progress": [0, 50]}
        result = TodoAnalyticsService.log_todo_update(
            self.user,
            self.todo,
            changed_fields
        )
        
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()
    
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_todo_complete(self, mock_setup_schema, mock_connect):
        """Todo完了イベントのログ"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        self.todo.progress = 100
        result = TodoAnalyticsService.log_todo_complete(self.user, self.todo)
        
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()
    
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_todo_delete(self, mock_setup_schema, mock_connect):
        """Todo削除イベントのログ"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = TodoAnalyticsService.log_todo_delete(
            self.user,
            self.todo,
            deletion_reason="completed"
        )
        
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()


# ================================
# TodoQStashService Tests
# ================================


class TodoQStashServiceTestCase(TestCase):
    """TodoQStashService のテスト"""

    @override_settings(
        QSTASH_TOKEN="test_token", WEBHOOK_BASE_URL="https://test.example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_upsert(self, mock_post):
        """ベクトルインデックス化（upsert）のキュー投入"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = TodoQStashService.queue_vector_indexing(1, operation="upsert")

        self.assertEqual(message_id, "msg_123")
        mock_post.assert_called_once()

    @override_settings(
        QSTASH_TOKEN="test_token", WEBHOOK_BASE_URL="https://test.example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_delete(self, mock_post):
        """ベクトルインデックス化（delete）のキュー投入"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_456"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = TodoQStashService.queue_vector_indexing(1, operation="delete")

        self.assertEqual(message_id, "msg_456")

    @override_settings(
        QSTASH_TOKEN="test_token", WEBHOOK_BASE_URL="https://test.example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_queue_bulk_vector_indexing(self, mock_post):
        """一括ベクトルインデックス化のキュー投入"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_bulk"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = TodoQStashService.queue_bulk_vector_indexing(1)

        self.assertEqual(message_id, "msg_bulk")


# ================================
# TodoEmbeddingService Tests
# ================================


class TodoEmbeddingServiceTestCase(TestCase):
    """TodoEmbeddingService のテスト"""

    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )

    def test_prepare_text(self):
        """テキスト準備"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=75,
        )

        text = TodoEmbeddingService.prepare_text(todo)

        self.assertIn("Test Todo", text)
        self.assertIn("高", text)
        self.assertIn("75%", text)

    def test_prepare_text_normalization(self):
        """テキスト正規化（スペース除去）"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test   Multiple   Spaces",
            priority=Todo.Priority.MEDIUM,
            progress=0,
        )

        text = TodoEmbeddingService.prepare_text(todo)

        self.assertNotIn("   ", text)


# ================================
# VectorService Tests
# ================================


class VectorServiceTestCase(TestCase):
    """VectorService のテスト"""

    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=50,
        )

    @patch("apps.common.services.base_vector.BaseVectorService._safe_upsert")
    @patch("apps.common.services.base_embedding.BaseEmbeddingService.embed_text")
    def test_add_todo(self, mock_embed, mock_upsert):
        """Todoをベクトルインデックスに追加"""
        mock_embed.return_value = [0.1, 0.2, 0.3]

        service = VectorService()
        service.add_todo(self.todo)

        mock_embed.assert_called_once()
        mock_upsert.assert_called_once()

    @patch("apps.common.services.base_vector.BaseVectorService._safe_delete")
    def test_delete_todo(self, mock_delete):
        """Todoをベクトルインデックスから削除"""
        service = VectorService()
        service.delete_todo(self.todo.id)

        mock_delete.assert_called_once_with([str(self.todo.id)])

    @patch("apps.common.services.base_vector.BaseVectorService._safe_query")
    @patch("apps.common.services.base_embedding.BaseEmbeddingService.embed_text")
    def test_search_similar(self, mock_embed, mock_query):
        """類似Todoの検索"""
        mock_embed.return_value = [0.1, 0.2, 0.3]

        mock_result = MagicMock()
        mock_result.id = "1"
        mock_result.score = 0.8
        mock_result.metadata = {"title": "Test", "priority": "HIGH", "progress": 50}
        mock_query.return_value = [mock_result]

        service = VectorService()
        results = service.search_similar("test query", self.user.id)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[0]["score"], 0.8)


# ================================
# TodoWebhookService Tests
# ================================


class TodoWebhookServiceTestCase(TestCase):
    """TodoWebhookService のテスト"""

    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        self.todo = Todo.objects.create(user=self.user, todo_title="Test Todo")

    @patch.object(VectorService, "add_todo")
    def test_handle_vector_indexing_upsert(self, mock_add_todo):
        """ベクトルインデックス化（upsert）の処理"""
        result = TodoWebhookService.handle_vector_indexing(self.todo.id, "upsert")

        self.assertEqual(result["todo_id"], self.todo.id)
        self.assertEqual(result["operation"], "upsert")
        mock_add_todo.assert_called_once()

    @patch.object(VectorService, "delete_todo")
    def test_handle_vector_indexing_delete(self, mock_delete_todo):
        """ベクトルインデックス化（delete）の処理"""
        result = TodoWebhookService.handle_vector_indexing(self.todo.id, "delete")

        self.assertEqual(result["todo_id"], self.todo.id)
        self.assertEqual(result["operation"], "delete")
        mock_delete_todo.assert_called_once_with(self.todo.id)

    @patch.object(VectorService, "add_todos_batch")
    def test_handle_bulk_vector_indexing(self, mock_add_batch):
        """一括ベクトルインデックス化の処理"""
        Todo.objects.create(user=self.user, todo_title="Todo 2")

        result = TodoWebhookService.handle_bulk_vector_indexing(self.user.id)

        self.assertEqual(result["user_id"], self.user.id)
        self.assertEqual(result["count"], 2)
        mock_add_batch.assert_called_once()

    def test_handle_bulk_vector_indexing_no_todos(self):
        """Todoなしの一括インデックス化"""
        new_user = User.objects.create_user(
            email="empty@example.com", password="pass123"
        )

        result = TodoWebhookService.handle_bulk_vector_indexing(new_user.id)

        self.assertEqual(result["count"], 0)
