"""
Todoアプリのサービステスト（pytest）
TodoQueryService, TodoStatsService, TodoCommandService,
TodoQStashService, TodoEmbeddingService, VectorService, TodoWebhookService のテスト
"""
import pytest
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import Http404
from django.test import override_settings

from apps.todos.models import Todo
from apps.todos.embedding_service import TodoEmbeddingService
from apps.todos.qstash_service import TodoQStashService
from apps.todos.service import TodoCommandService, TodoQueryService, TodoStatsService
from apps.todos.vector_service import VectorService
from apps.todos.webhook_service import TodoWebhookService

User = get_user_model()


# ================================
# TodoQueryService Tests
# ================================

@pytest.mark.django_db
class TestTodoQueryService:
    """TodoQueryService のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
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

        assert todos.count() == 1
        assert todos.first() == self.todo1

    def test_get_user_todos_isolation(self):
        """ユーザーは自分のTodoのみ取得可能"""
        todos = TodoQueryService.get_user_todos(self.user1)

        assert self.todo2 not in todos

    def test_get_todo_by_id(self):
        """IDでTodo取得"""
        todo = TodoQueryService.get_todo_by_id(self.todo1.id, self.user1)

        assert todo == self.todo1

    def test_get_todo_by_id_wrong_user(self):
        """間違ったユーザーではNoneを返す"""
        todo = TodoQueryService.get_todo_by_id(self.todo1.id, self.user2)

        assert todo is None

    def test_get_todo_or_404(self):
        """Todo取得または404"""
        todo = TodoQueryService.get_todo_or_404(self.todo1.id, self.user1)
        assert todo == self.todo1

        with pytest.raises(Http404):
            TodoQueryService.get_todo_or_404(self.todo1.id, self.user2)


# ================================
# TodoStatsService Tests
# ================================

@pytest.mark.django_db
class TestTodoStatsService:
    """TodoStatsService のテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        cache.clear()
        yield
        cache.clear()

    def test_get_priority_stats(self):
        """優先度統計の取得"""
        Todo.objects.create(user=self.user, todo_title="High1", priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user, todo_title="High2", priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user, todo_title="Low1", priority=Todo.Priority.LOW)

        stats = TodoStatsService.get_priority_stats(self.user)

        high_stat = next((s for s in stats if s["priority"] == "HIGH"), None)
        low_stat = next((s for s in stats if s["priority"] == "LOW"), None)

        assert high_stat["count"] == 2
        assert low_stat["count"] == 1

    def test_get_progress_stats(self):
        """進捗統計の取得"""
        Todo.objects.create(user=self.user, todo_title="T1", progress=10)
        Todo.objects.create(user=self.user, todo_title="T2", progress=30)
        Todo.objects.create(user=self.user, todo_title="T3", progress=90)

        stats = TodoStatsService.get_progress_stats(self.user)

        assert stats["range_0_20"] == 1
        assert stats["range_21_40"] == 1
        assert stats["range_81_100"] == 1

    def test_stats_caching(self):
        """統計がキャッシュされる"""
        Todo.objects.create(user=self.user, todo_title="Test", priority=Todo.Priority.HIGH)

        stats1 = TodoStatsService.get_priority_stats(self.user)
        Todo.objects.create(user=self.user, todo_title="Test2", priority=Todo.Priority.HIGH)
        stats2 = TodoStatsService.get_priority_stats(self.user)

        assert stats1 == stats2

    def test_invalidate_stats_cache(self):
        """キャッシュの無効化"""
        Todo.objects.create(user=self.user, todo_title="Test")

        TodoStatsService.get_priority_stats(self.user)
        TodoStatsService.get_progress_stats(self.user)
        TodoStatsService.invalidate_stats_cache(self.user.id)

        cache_key_priority = TodoStatsService._get_stats_cache_key(self.user.id, "priority")
        cache_key_progress = TodoStatsService._get_stats_cache_key(self.user.id, "progress")

        assert cache.get(cache_key_priority) is None
        assert cache.get(cache_key_progress) is None


# ================================
# TodoCommandService Tests
# ================================

@pytest.mark.django_db
class TestTodoCommandService:
    """TodoCommandService のテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        cache.clear()
        yield
        cache.clear()

    @override_settings(TESTING=True)
    def test_create_todo(self):
        """Todo作成"""
        data = {"todo_title": "New Todo", "priority": "HIGH", "progress": 0}

        todo = TodoCommandService.create_todo(self.user, data)

        assert todo.todo_title == "New Todo"
        assert todo.priority == "HIGH"
        assert todo.user == self.user

    @override_settings(TESTING=True)
    def test_update_todo(self):
        """Todo更新"""
        todo = Todo.objects.create(user=self.user, todo_title="Original", progress=0)

        updated = TodoCommandService.update_todo(
            todo.id, self.user, {"todo_title": "Updated", "progress": 50}
        )

        assert updated.todo_title == "Updated"
        assert updated.progress == 50

    @override_settings(TESTING=True)
    def test_update_todo_wrong_user(self):
        """間違ったユーザーでの更新は404"""
        other_user = User.objects.create_user(
            email="other@example.com", password="pass123"
        )
        todo = Todo.objects.create(user=self.user, todo_title="Test")

        with pytest.raises(Http404):
            TodoCommandService.update_todo(todo.id, other_user, {"todo_title": "Hacked"})

    @override_settings(TESTING=True)
    def test_delete_todo(self):
        """Todo削除"""
        todo = Todo.objects.create(user=self.user, todo_title="Delete Me")
        todo_id = todo.id

        TodoCommandService.delete_todo(todo_id, self.user)

        assert not Todo.objects.filter(id=todo_id).exists()

    @override_settings(TESTING=True)
    def test_cache_invalidation_on_create(self):
        """作成時にキャッシュが無効化される"""
        TodoStatsService.get_priority_stats(self.user)

        TodoCommandService.create_todo(
            self.user, {"todo_title": "Test", "priority": "HIGH", "progress": 0}
        )

        cache_key = TodoStatsService._get_stats_cache_key(self.user.id, "priority")
        assert cache.get(cache_key) is None


# ================================
# TodoQStashService Tests
# ================================

@pytest.mark.django_db
class TestTodoQStashService:
    """TodoQStashService のテスト"""

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com"
    )
    def test_queue_vector_indexing_upsert(self, mocker):
        """ベクトルインデックス化（upsert）のキュー投入"""
        mock_post = mocker.patch("apps.common.infrastructure.qstash_client.requests.post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = TodoQStashService.queue_vector_indexing(1, operation="upsert")

        assert message_id == "msg_123"
        mock_post.assert_called_once()

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com"
    )
    def test_queue_vector_indexing_delete(self, mocker):
        """ベクトルインデックス化（delete）のキュー投入"""
        mock_post = mocker.patch("apps.common.infrastructure.qstash_client.requests.post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_456"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = TodoQStashService.queue_vector_indexing(1, operation="delete")

        assert message_id == "msg_456"

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com"
    )
    def test_queue_bulk_vector_indexing(self, mocker):
        """一括ベクトルインデックス化のキュー投入"""
        mock_post = mocker.patch("apps.common.infrastructure.qstash_client.requests.post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_bulk"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = TodoQStashService.queue_bulk_vector_indexing(1)

        assert message_id == "msg_bulk"


# ================================
# TodoEmbeddingService Tests
# ================================

@pytest.mark.django_db
class TestTodoEmbeddingService:
    """TodoEmbeddingService のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
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

        assert "Test Todo" in text
        assert "高" in text
        assert "75%" in text

    def test_prepare_text_normalization(self):
        """テキスト正規化（スペース除去）"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test   Multiple   Spaces",
            priority=Todo.Priority.MEDIUM,
            progress=0,
        )

        text = TodoEmbeddingService.prepare_text(todo)

        assert "   " not in text


# ================================
# VectorService Tests
# ================================

@pytest.mark.django_db
class TestVectorService:
    """VectorService のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=50,
        )

    def test_add_todo(self, mocker):
        """Todoをベクトルインデックスに追加"""
        mock_embed = mocker.patch(
            "apps.common.services.base_embedding.BaseEmbeddingService.embed_text",
            return_value=[0.1, 0.2, 0.3]
        )
        mock_upsert = mocker.patch(
            "apps.common.services.base_vector.BaseVectorService._safe_upsert"
        )

        service = VectorService()
        service.add_todo(self.todo)

        mock_embed.assert_called_once()
        mock_upsert.assert_called_once()

    def test_delete_todo(self, mocker):
        """Todoをベクトルインデックスから削除"""
        mock_delete = mocker.patch(
            "apps.common.services.base_vector.BaseVectorService._safe_delete"
        )

        service = VectorService()
        service.delete_todo(self.todo.id)

        mock_delete.assert_called_once_with([str(self.todo.id)])

    def test_search_similar(self, mocker):
        """類似Todoの検索"""
        mocker.patch(
            "apps.common.services.base_embedding.BaseEmbeddingService.embed_text",
            return_value=[0.1, 0.2, 0.3]
        )
        mock_result = MagicMock()
        mock_result.id = "1"
        mock_result.score = 0.8
        mock_result.metadata = {"title": "Test", "priority": "HIGH", "progress": 50}
        mocker.patch(
            "apps.common.services.base_vector.BaseVectorService._safe_query",
            return_value=[mock_result]
        )

        service = VectorService()
        results = service.search_similar("test query", self.user.id)

        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["score"] == 0.8


# ================================
# TodoWebhookService Tests
# ================================

@pytest.mark.django_db
class TestTodoWebhookService:
    """TodoWebhookService のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="pass123"
        )
        self.todo = Todo.objects.create(user=self.user, todo_title="Test Todo")

    def test_handle_vector_indexing_upsert(self, mocker):
        """ベクトルインデックス化（upsert）の処理"""
        mock_add = mocker.patch.object(VectorService, "add_todo")

        result = TodoWebhookService.handle_vector_indexing(self.todo.id, "upsert")

        assert result["todo_id"] == self.todo.id
        assert result["operation"] == "upsert"
        mock_add.assert_called_once()

    def test_handle_vector_indexing_delete(self, mocker):
        """ベクトルインデックス化（delete）の処理"""
        mock_delete = mocker.patch.object(VectorService, "delete_todo")

        result = TodoWebhookService.handle_vector_indexing(self.todo.id, "delete")

        assert result["todo_id"] == self.todo.id
        assert result["operation"] == "delete"
        mock_delete.assert_called_once_with(self.todo.id)

    def test_handle_bulk_vector_indexing(self, mocker):
        """一括ベクトルインデックス化の処理"""
        mock_batch = mocker.patch.object(VectorService, "add_todos_batch")
        Todo.objects.create(user=self.user, todo_title="Todo 2")

        result = TodoWebhookService.handle_bulk_vector_indexing(self.user.id)

        assert result["user_id"] == self.user.id
        assert result["count"] == 2
        mock_batch.assert_called_once()

    def test_handle_bulk_vector_indexing_no_todos(self):
        """Todoなしの一括インデックス化"""
        new_user = User.objects.create_user(
            email="empty@example.com", password="pass123"
        )

        result = TodoWebhookService.handle_bulk_vector_indexing(new_user.id)

        assert result["count"] == 0