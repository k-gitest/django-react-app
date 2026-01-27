"""
Tests for todos app
Models, Serializers, Services, Views, Webhooks
"""
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

from apps.todos.models import Todo
from apps.todos.serializers import (
    TodoSerializer,
    TodoSearchParamsSerializer,
    VectorIndexingWebhookSerializer,
    BulkVectorIndexingWebhookSerializer
)
from apps.todos.service import (
    TodoQueryService,
    TodoCommandService,
    TodoStatsService,
    TodoSearchService
)
from apps.todos.analytics_service import TodoAnalyticsService
from apps.todos.qstash_service import TodoQStashService
from apps.todos.embedding_service import TodoEmbeddingService
from apps.todos.vector_service import VectorService
from apps.todos.webhook_service import TodoWebhookService
from apps.common.exceptions import (
    QStashError,
    AnalyticsError,
    VectorError,
    EmbeddingError
)


User = get_user_model()


# ================================
# Model Tests
# ================================

class TodoModelTestCase(TestCase):
    """Tests for Todo model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    def test_create_todo(self):
        """Test creating a todo"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=50
        )
        
        self.assertEqual(todo.todo_title, "Test Todo")
        self.assertEqual(todo.priority, Todo.Priority.HIGH)
        self.assertEqual(todo.progress, 50)
        self.assertEqual(todo.user, self.user)

    def test_default_priority(self):
        """Test default priority is MEDIUM"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Default Priority Todo"
        )
        
        self.assertEqual(todo.priority, Todo.Priority.MEDIUM)

    def test_default_progress(self):
        """Test default progress is 0"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Default Progress Todo"
        )
        
        self.assertEqual(todo.progress, 0)

    def test_priority_choices(self):
        """Test priority choices are correct"""
        self.assertEqual(Todo.Priority.LOW, 'LOW')
        self.assertEqual(Todo.Priority.MEDIUM, 'MEDIUM')
        self.assertEqual(Todo.Priority.HIGH, 'HIGH')

    def test_str_representation(self):
        """Test __str__ method"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="String Test"
        )
        
        self.assertEqual(str(todo), "String Test")

    def test_ordering(self):
        """Test todos are ordered by created_at descending"""
        todo1 = Todo.objects.create(user=self.user, todo_title="First")
        todo2 = Todo.objects.create(user=self.user, todo_title="Second")
        
        todos = list(Todo.objects.all())
        self.assertEqual(todos[0], todo2)
        self.assertEqual(todos[1], todo1)

    def test_user_cascade_delete(self):
        """Test todos are deleted when user is deleted"""
        todo = Todo.objects.create(user=self.user, todo_title="Test")
        todo_id = todo.id
        
        self.user.delete()
        
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())


# ================================
# Serializer Tests
# ================================

class TodoSerializerTestCase(TestCase):
    """Tests for TodoSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    def test_serializer_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'todo_title': 'Test Todo',
            'priority': 'HIGH',
            'progress': 75
        }
        
        serializer = TodoSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_title_validation_empty(self):
        """Test title validation rejects empty string"""
        data = {
            'todo_title': '   ',
            'priority': 'MEDIUM',
            'progress': 0
        }
        
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('todo_title', serializer.errors)

    def test_serializer_title_validation_too_long(self):
        """Test title validation rejects too long title"""
        data = {
            'todo_title': 'A' * 201,
            'priority': 'MEDIUM',
            'progress': 0
        }
        
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('todo_title', serializer.errors)

    def test_serializer_title_trimming(self):
        """Test title is trimmed"""
        data = {
            'todo_title': '  Test Todo  ',
            'priority': 'MEDIUM',
            'progress': 0
        }
        
        serializer = TodoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['todo_title'], 'Test Todo')

    def test_serializer_progress_validation_negative(self):
        """Test progress validation rejects negative values"""
        data = {
            'todo_title': 'Test',
            'priority': 'MEDIUM',
            'progress': -10
        }
        
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('progress', serializer.errors)

    def test_serializer_progress_validation_over_100(self):
        """Test progress validation rejects values over 100"""
        data = {
            'todo_title': 'Test',
            'priority': 'MEDIUM',
            'progress': 150
        }
        
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('progress', serializer.errors)

    def test_serializer_priority_validation(self):
        """Test priority validation"""
        data = {
            'todo_title': 'Test',
            'priority': 'INVALID',
            'progress': 0
        }
        
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('priority', serializer.errors)

    def test_serializer_read_only_fields(self):
        """Test read-only fields"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test"
        )
        
        serializer = TodoSerializer(todo)
        self.assertIn('id', serializer.data)
        self.assertIn('user', serializer.data)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)


class TodoSearchParamsSerializerTestCase(TestCase):
    """Tests for TodoSearchParamsSerializer"""

    def test_valid_search_params(self):
        """Test valid search parameters"""
        data = {
            'q': 'test query',
            'top_k': 10,
            'min_score': 0.7
        }
        
        serializer = TodoSearchParamsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_default_values(self):
        """Test default values"""
        data = {'q': 'test'}
        
        serializer = TodoSearchParamsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['top_k'], 5)
        self.assertEqual(serializer.validated_data['min_score'], 0.5)

    def test_query_required(self):
        """Test query is required"""
        data = {}
        
        serializer = TodoSearchParamsSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('q', serializer.errors)

    def test_query_trimming(self):
        """Test query is trimmed"""
        data = {'q': '  test query  '}
        
        serializer = TodoSearchParamsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['q'], 'test query')


class VectorIndexingWebhookSerializerTestCase(TestCase):
    """Tests for VectorIndexingWebhookSerializer"""

    def test_valid_upsert(self):
        """Test valid upsert operation"""
        data = {
            'todo_id': 1,
            'operation': 'upsert'
        }
        
        serializer = VectorIndexingWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_delete(self):
        """Test valid delete operation"""
        data = {
            'todo_id': 1,
            'operation': 'delete'
        }
        
        serializer = VectorIndexingWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_default_operation(self):
        """Test default operation is upsert"""
        data = {'todo_id': 1}
        
        serializer = VectorIndexingWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['operation'], 'upsert')

    def test_invalid_operation(self):
        """Test invalid operation"""
        data = {
            'todo_id': 1,
            'operation': 'invalid'
        }
        
        serializer = VectorIndexingWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())


# ================================
# Service Tests - TodoQueryService
# ================================

class TodoQueryServiceTestCase(TestCase):
    """Tests for TodoQueryService"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="pass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="pass123"
        )
        self.todo1 = Todo.objects.create(
            user=self.user1,
            todo_title="User1 Todo"
        )
        self.todo2 = Todo.objects.create(
            user=self.user2,
            todo_title="User2 Todo"
        )

    def test_get_user_todos(self):
        """Test getting user's todos"""
        todos = TodoQueryService.get_user_todos(self.user1)
        
        self.assertEqual(todos.count(), 1)
        self.assertEqual(todos.first(), self.todo1)

    def test_get_user_todos_isolation(self):
        """Test users can only see their own todos"""
        todos = TodoQueryService.get_user_todos(self.user1)
        
        self.assertNotIn(self.todo2, todos)

    def test_get_todo_by_id(self):
        """Test getting todo by id"""
        todo = TodoQueryService.get_todo_by_id(self.todo1.id, self.user1)
        
        self.assertEqual(todo, self.todo1)

    def test_get_todo_by_id_wrong_user(self):
        """Test getting todo by id with wrong user returns None"""
        todo = TodoQueryService.get_todo_by_id(self.todo1.id, self.user2)
        
        self.assertIsNone(todo)

    def test_get_todo_or_404(self):
        """Test getting todo or 404"""
        from django.http import Http404
        
        todo = TodoQueryService.get_todo_or_404(self.todo1.id, self.user1)
        self.assertEqual(todo, self.todo1)
        
        with self.assertRaises(Http404):
            TodoQueryService.get_todo_or_404(self.todo1.id, self.user2)


# ================================
# Service Tests - TodoStatsService
# ================================

class TodoStatsServiceTestCase(TestCase):
    """Tests for TodoStatsService"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        # Clear cache
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_get_priority_stats(self):
        """Test priority statistics"""
        Todo.objects.create(user=self.user, todo_title="High1", priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user, todo_title="High2", priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user, todo_title="Low1", priority=Todo.Priority.LOW)
        
        stats = TodoStatsService.get_priority_stats(self.user)
        
        high_stat = next((s for s in stats if s['priority'] == 'HIGH'), None)
        low_stat = next((s for s in stats if s['priority'] == 'LOW'), None)
        
        self.assertEqual(high_stat['count'], 2)
        self.assertEqual(low_stat['count'], 1)

    def test_get_progress_stats(self):
        """Test progress statistics"""
        Todo.objects.create(user=self.user, todo_title="T1", progress=10)
        Todo.objects.create(user=self.user, todo_title="T2", progress=30)
        Todo.objects.create(user=self.user, todo_title="T3", progress=90)
        
        stats = TodoStatsService.get_progress_stats(self.user)
        
        self.assertEqual(stats['range_0_20'], 1)
        self.assertEqual(stats['range_21_40'], 1)
        self.assertEqual(stats['range_81_100'], 1)

    def test_stats_caching(self):
        """Test stats are cached"""
        Todo.objects.create(user=self.user, todo_title="Test", priority=Todo.Priority.HIGH)
        
        # First call - should hit database
        stats1 = TodoStatsService.get_priority_stats(self.user)
        
        # Create another todo
        Todo.objects.create(user=self.user, todo_title="Test2", priority=Todo.Priority.HIGH)
        
        # Second call - should return cached value
        stats2 = TodoStatsService.get_priority_stats(self.user)
        
        # Stats should be the same (cached)
        self.assertEqual(stats1, stats2)

    def test_invalidate_stats_cache(self):
        """Test cache invalidation"""
        Todo.objects.create(user=self.user, todo_title="Test")
        
        # Cache stats
        TodoStatsService.get_priority_stats(self.user)
        TodoStatsService.get_progress_stats(self.user)
        
        # Invalidate
        TodoStatsService.invalidate_stats_cache(self.user.id)
        
        # Check cache is cleared
        cache_key_priority = TodoStatsService._get_stats_cache_key(self.user.id, "priority")
        cache_key_progress = TodoStatsService._get_stats_cache_key(self.user.id, "progress")
        
        self.assertIsNone(cache.get(cache_key_priority))
        self.assertIsNone(cache.get(cache_key_progress))


# ================================
# Service Tests - TodoCommandService
# ================================

class TodoCommandServiceTestCase(TestCase):
    """Tests for TodoCommandService"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    @override_settings(TESTING=True)
    def test_create_todo(self):
        """Test creating a todo"""
        data = {
            'todo_title': 'New Todo',
            'priority': 'HIGH',
            'progress': 0
        }
        
        todo = TodoCommandService.create_todo(self.user, data)
        
        self.assertEqual(todo.todo_title, 'New Todo')
        self.assertEqual(todo.priority, 'HIGH')
        self.assertEqual(todo.user, self.user)

    @override_settings(TESTING=True)
    def test_update_todo(self):
        """Test updating a todo"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Original",
            progress=0
        )
        
        updated = TodoCommandService.update_todo(
            todo.id,
            self.user,
            {'todo_title': 'Updated', 'progress': 50}
        )
        
        self.assertEqual(updated.todo_title, 'Updated')
        self.assertEqual(updated.progress, 50)

    @override_settings(TESTING=True)
    def test_update_todo_wrong_user(self):
        """Test updating todo with wrong user raises 404"""
        from django.http import Http404
        
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123"
        )
        todo = Todo.objects.create(user=self.user, todo_title="Test")
        
        with self.assertRaises(Http404):
            TodoCommandService.update_todo(
                todo.id,
                other_user,
                {'todo_title': 'Hacked'}
            )

    @override_settings(TESTING=True)
    def test_delete_todo(self):
        """Test deleting a todo"""
        todo = Todo.objects.create(user=self.user, todo_title="Delete Me")
        todo_id = todo.id
        
        TodoCommandService.delete_todo(todo_id, self.user)
        
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    @override_settings(TESTING=True)
    def test_cache_invalidation_on_create(self):
        """Test cache is invalidated on create"""
        # Cache stats
        TodoStatsService.get_priority_stats(self.user)
        
        # Create todo
        TodoCommandService.create_todo(
            self.user,
            {'todo_title': 'Test', 'priority': 'HIGH', 'progress': 0}
        )
        
        # Cache should be invalidated
        cache_key = TodoStatsService._get_stats_cache_key(self.user.id, "priority")
        self.assertIsNone(cache.get(cache_key))


# ================================
# Service Tests - TodoAnalyticsService
# ================================

class TodoAnalyticsServiceTestCase(TestCase):
    """Tests for TodoAnalyticsService"""

    def setUp(self):
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
        TodoAnalyticsService._client = None

    def tearDown(self):
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        TodoAnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_todo_create(self, mock_setup_schema, mock_connect):
        """Test logging todo create event"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = TodoAnalyticsService.log_todo_create(self.user, self.todo)
        
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_todo_update(self, mock_setup_schema, mock_connect):
        """Test logging todo update event"""
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
        """Test logging todo complete event"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        self.todo.progress = 100
        result = TodoAnalyticsService.log_todo_complete(self.user, self.todo)
        
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_todo_delete(self, mock_setup_schema, mock_connect):
        """Test logging todo delete event"""
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
# Service Tests - TodoQStashService
# ================================

class TodoQStashServiceTestCase(TestCase):
    """Tests for TodoQStashService"""

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_upsert(self, mock_post):
        """Test queueing vector indexing (upsert)"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        message_id = TodoQStashService.queue_vector_indexing(1, operation="upsert")
        
        self.assertEqual(message_id, "msg_123")
        mock_post.assert_called_once()

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_delete(self, mock_post):
        """Test queueing vector indexing (delete)"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_456"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        message_id = TodoQStashService.queue_vector_indexing(1, operation="delete")
        
        self.assertEqual(message_id, "msg_456")

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_queue_bulk_vector_indexing(self, mock_post):
        """Test queueing bulk vector indexing"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_bulk"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        message_id = TodoQStashService.queue_bulk_vector_indexing(1)
        
        self.assertEqual(message_id, "msg_bulk")


# ================================
# Service Tests - TodoEmbeddingService
# ================================

class TodoEmbeddingServiceTestCase(TestCase):
    """Tests for TodoEmbeddingService"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )

    def test_prepare_text(self):
        """Test text preparation"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=75
        )
        
        # prepare_text is a static method (no self parameter)
        text = TodoEmbeddingService.prepare_text(todo)
        
        self.assertIn("Test Todo", text)
        self.assertIn("高", text)  # HIGH priority display
        self.assertIn("75%", text)

    def test_prepare_text_normalization(self):
        """Test text normalization removes extra spaces"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test   Multiple   Spaces",
            priority=Todo.Priority.MEDIUM,
            progress=0
        )
        
        text = TodoEmbeddingService.prepare_text(todo)
        
        # Multiple spaces should be normalized to single space
        self.assertNotIn("   ", text)


# ================================
# Service Tests - VectorService
# ================================

class VectorServiceTestCase(TestCase):
    """Tests for VectorService"""

    def setUp(self):
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

    @patch("apps.common.services.base_vector.BaseVectorService._safe_upsert")
    @patch("apps.common.services.base_embedding.BaseEmbeddingService.embed_text")
    def test_add_todo(self, mock_embed, mock_upsert):
        """Test adding todo to vector index"""
        mock_embed.return_value = [0.1, 0.2, 0.3]
        
        service = VectorService()
        service.add_todo(self.todo)
        
        mock_embed.assert_called_once()
        mock_upsert.assert_called_once()

    @patch("apps.common.services.base_vector.BaseVectorService._safe_delete")
    def test_delete_todo(self, mock_delete):
        """Test deleting todo from vector index"""
        service = VectorService()
        service.delete_todo(self.todo.id)
        
        mock_delete.assert_called_once_with([str(self.todo.id)])

    @patch("apps.common.services.base_vector.BaseVectorService._safe_query")
    @patch("apps.common.services.base_embedding.BaseEmbeddingService.embed_text")
    def test_search_similar(self, mock_embed, mock_query):
        """Test searching similar todos"""
        mock_embed.return_value = [0.1, 0.2, 0.3]
        
        mock_result = MagicMock()
        mock_result.id = "1"
        mock_result.score = 0.8
        mock_result.metadata = {
            "title": "Test",
            "priority": "HIGH",
            "progress": 50
        }
        mock_query.return_value = [mock_result]
        
        service = VectorService()
        results = service.search_similar("test query", self.user.id)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 1)
        self.assertEqual(results[0]['score'], 0.8)


# ================================
# Service Tests - TodoWebhookService
# ================================

class TodoWebhookServiceTestCase(TestCase):
    """Tests for TodoWebhookService"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo"
        )

    @patch.object(VectorService, 'add_todo')
    def test_handle_vector_indexing_upsert(self, mock_add_todo):
        """Test handling vector indexing upsert"""
        result = TodoWebhookService.handle_vector_indexing(
            self.todo.id,
            "upsert"
        )
        
        self.assertEqual(result['todo_id'], self.todo.id)
        self.assertEqual(result['operation'], 'upsert')
        mock_add_todo.assert_called_once()

    @patch.object(VectorService, 'delete_todo')
    def test_handle_vector_indexing_delete(self, mock_delete_todo):
        """Test handling vector indexing delete"""
        result = TodoWebhookService.handle_vector_indexing(
            self.todo.id,
            "delete"
        )
        
        self.assertEqual(result['todo_id'], self.todo.id)
        self.assertEqual(result['operation'], 'delete')
        mock_delete_todo.assert_called_once_with(self.todo.id)

    @patch.object(VectorService, 'add_todos_batch')
    def test_handle_bulk_vector_indexing(self, mock_add_batch):
        """Test handling bulk vector indexing"""
        Todo.objects.create(user=self.user, todo_title="Todo 2")
        
        result = TodoWebhookService.handle_bulk_vector_indexing(self.user.id)
        
        self.assertEqual(result['user_id'], self.user.id)
        self.assertEqual(result['count'], 2)
        mock_add_batch.assert_called_once()

    def test_handle_bulk_vector_indexing_no_todos(self):
        """Test bulk indexing with no todos"""
        new_user = User.objects.create_user(
            email="empty@example.com",
            password="pass123"
        )
        
        result = TodoWebhookService.handle_bulk_vector_indexing(new_user.id)
        
        self.assertEqual(result['count'], 0)


# ================================
# View Tests
# ================================

class TodoViewSetTestCase(APITestCase):
    """Tests for TodoViewSet"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    @override_settings(TESTING=True)
    def test_list_todos(self):
        """Test listing todos"""
        Todo.objects.create(user=self.user, todo_title="Todo 1")
        Todo.objects.create(user=self.user, todo_title="Todo 2")
        
        response = self.client.get("/api/v1/todos/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    @override_settings(TESTING=True)
    def test_create_todo(self):
        """Test creating a todo"""
        data = {
            'todo_title': 'New Todo',
            'priority': 'HIGH',
            'progress': 0
        }
        
        response = self.client.post("/api/v1/todos/", data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['todo_title'], 'New Todo')
        self.assertTrue(Todo.objects.filter(todo_title='New Todo').exists())

    @override_settings(TESTING=True)
    def test_update_todo(self):
        """Test updating a todo"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Original",
            progress=0
        )
        
        data = {'todo_title': 'Updated', 'progress': 50}
        response = self.client.patch(
            f"/api/v1/todos/{todo.id}/",
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['todo_title'], 'Updated')
        self.assertEqual(response.data['progress'], 50)

    @override_settings(TESTING=True)
    def test_delete_todo(self):
        """Test deleting a todo"""
        todo = Todo.objects.create(user=self.user, todo_title="Delete Me")
        
        response = self.client.delete(f"/api/v1/todos/{todo.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Todo.objects.filter(id=todo.id).exists())

    def test_get_stats(self):
        """Test getting priority stats"""
        Todo.objects.create(user=self.user, todo_title="T1", priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user, todo_title="T2", priority=Todo.Priority.HIGH)
        
        response = self.client.get("/api/v1/todos/stats/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_progress_stats(self):
        """Test getting progress stats"""
        Todo.objects.create(user=self.user, todo_title="T1", progress=10)
        Todo.objects.create(user=self.user, todo_title="T2", progress=90)
        
        response = self.client.get("/api/v1/todos/progress-stats/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('range_0_20', response.data)

    def test_user_isolation(self):
        """Test users can only access their own todos"""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123"
        )
        other_todo = Todo.objects.create(
            user=other_user,
            todo_title="Other User Todo"
        )
        
        response = self.client.get(f"/api/v1/todos/{other_todo.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TodoWebhookViewsTestCase(APITestCase):
    """Tests for todo webhook views"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo"
        )

    @patch("apps.todos.views.TodoWebhookService.handle_vector_indexing")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_vector_indexing_webhook(self, mock_verify, mock_handle):
        """Test vector indexing webhook"""
        mock_verify.return_value = True
        mock_handle.return_value = {
            "message": "Vector indexed successfully",
            "todo_id": self.todo.id,
            "operation": "upsert"
        }
        
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing",
            {
                'todo_id': self.todo.id,
                'operation': 'upsert'
            },
            format='json',
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_handle.assert_called_once_with(
            todo_id=self.todo.id,
            operation='upsert'
        )

    @patch("apps.todos.views.TodoWebhookService.handle_bulk_vector_indexing")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_bulk_vector_indexing_webhook(self, mock_verify, mock_handle):
        """Test bulk vector indexing webhook"""
        mock_verify.return_value = True
        mock_handle.return_value = {
            "message": "Bulk indexing completed",
            "user_id": self.user.id,
            "count": 1
        }
        
        response = self.client.post(
            "/api/v1/webhooks/bulk-vector-indexing",
            {'user_id': self.user.id},
            format='json',
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_handle.assert_called_once_with(user_id=self.user.id)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_invalid_signature(self, mock_verify):
        """Test webhook with invalid signature"""
        mock_verify.return_value = False
        
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing",
            {'todo_id': 1, 'operation': 'upsert'},
            format='json',
            HTTP_UPSTASH_SIGNATURE="v1=invalid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)