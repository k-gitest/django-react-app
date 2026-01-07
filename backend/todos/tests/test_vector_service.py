"""
Tests for VectorService
"""
from unittest.mock import patch, MagicMock, PropertyMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from todos.vector_service import VectorService
from todos.models import Todo

User = get_user_model()


class VectorServiceTestCase(TestCase):
    """Tests for VectorService"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="会議資料の作成",
            priority="HIGH",
            progress=50
        )

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_add_todo_success(self, mock_embed, mock_index_class):
        """Test successfully adding a todo to vector index"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.1] * 768}
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act
        service.add_todo(self.todo)

        # Assert
        mock_embed.assert_called_once()
        mock_index.upsert.assert_called_once()
        
        # Verify upsert arguments
        call_args = mock_index.upsert.call_args[1]["vectors"]
        self.assertEqual(call_args[0][0], str(self.todo.id))  # ID
        self.assertEqual(len(call_args[0][1]), 768)  # Embedding
        self.assertEqual(call_args[0][2]["title"], "会議資料の作成")  # Metadata
        self.assertEqual(call_args[0][2]["user_id"], self.user.id)
        self.assertEqual(call_args[0][2]["priority"], "HIGH")
        self.assertEqual(call_args[0][2]["progress"], 50)

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_add_todo_embedding_error(self, mock_embed, mock_index_class):
        """Test adding todo with embedding error"""
        # Arrange
        mock_embed.side_effect = Exception("Embedding API Error")
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act & Assert
        with self.assertRaises(Exception) as context:
            service.add_todo(self.todo)

        self.assertIn("Embedding API Error", str(context.exception))
        # Upsert should not be called if embedding fails
        mock_index.upsert.assert_not_called()

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_update_todo_success(self, mock_embed, mock_index_class):
        """Test successfully updating a todo in vector index"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.2] * 768}
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act
        service.update_todo(self.todo)

        # Assert
        # Should delete first, then add
        mock_index.delete.assert_called_once_with(ids=[str(self.todo.id)])
        mock_index.upsert.assert_called_once()

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    def test_delete_todo_success(self, mock_index_class):
        """Test successfully deleting a todo from vector index"""
        # Arrange
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act
        service.delete_todo(self.todo.id)

        # Assert
        mock_index.delete.assert_called_once_with(ids=[str(self.todo.id)])

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    def test_delete_todo_error(self, mock_index_class):
        """Test deleting todo with error"""
        # Arrange
        mock_index = MagicMock()
        mock_index.delete.side_effect = Exception("Delete Error")
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act & Assert
        with self.assertRaises(Exception) as context:
            service.delete_todo(self.todo.id)

        self.assertIn("Delete Error", str(context.exception))

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_search_similar_success(self, mock_embed, mock_index_class):
        """Test successful semantic search"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.3] * 768}
        
        # Mock search results
        mock_result_1 = MagicMock()
        mock_result_1.id = "1"
        mock_result_1.score = 0.85
        mock_result_1.metadata = {
            "title": "会議資料の作成",
            "priority": "HIGH",
            "progress": 50
        }
        
        mock_result_2 = MagicMock()
        mock_result_2.id = "2"
        mock_result_2.score = 0.75
        mock_result_2.metadata = {
            "title": "プレゼン準備",
            "priority": "MEDIUM",
            "progress": 30
        }
        
        mock_index = MagicMock()
        mock_index.query.return_value = [mock_result_1, mock_result_2]
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act
        results = service.search_similar("明日の会議", user_id=self.user.id, top_k=5)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[0]["score"], 0.85)
        self.assertEqual(results[0]["title"], "会議資料の作成")
        self.assertEqual(results[1]["id"], 2)
        self.assertEqual(results[1]["score"], 0.75)

        # Verify query was called with correct parameters
        mock_index.query.assert_called_once()
        call_kwargs = mock_index.query.call_args[1]
        self.assertEqual(len(call_kwargs["vector"]), 768)
        self.assertEqual(call_kwargs["top_k"], 5)
        self.assertTrue(call_kwargs["include_metadata"])
        self.assertEqual(call_kwargs["filter"], f"user_id = {self.user.id}")

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_search_similar_with_min_score_filter(self, mock_embed, mock_index_class):
        """Test search with minimum score filtering"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.3] * 768}
        
        # Mock results with varying scores
        mock_result_high = MagicMock()
        mock_result_high.id = "1"
        mock_result_high.score = 0.85
        mock_result_high.metadata = {"title": "High", "priority": "HIGH", "progress": 50}
        
        mock_result_low = MagicMock()
        mock_result_low.id = "2"
        mock_result_low.score = 0.40
        mock_result_low.metadata = {"title": "Low", "priority": "LOW", "progress": 10}
        
        mock_index = MagicMock()
        mock_index.query.return_value = [mock_result_high, mock_result_low]
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act - Filter with min_score=0.5
        results = service.search_similar("test query", user_id=self.user.id, min_score=0.5)

        # Assert - Only high score result should be returned
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[0]["score"], 0.85)

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_search_similar_empty_results(self, mock_embed, mock_index_class):
        """Test search with no results"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.3] * 768}
        mock_index = MagicMock()
        mock_index.query.return_value = []
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act
        results = service.search_similar("test", user_id=self.user.id)

        # Assert
        self.assertEqual(len(results), 0)

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_search_similar_embedding_error(self, mock_embed, mock_index_class):
        """Test search with embedding error"""
        # Arrange
        mock_embed.side_effect = Exception("Embedding Error")
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act & Assert
        with self.assertRaises(Exception) as context:
            service.search_similar("test", user_id=self.user.id)

        self.assertIn("Embedding Error", str(context.exception))
        # Query should not be called if embedding fails
        mock_index.query.assert_not_called()

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_add_todos_batch_success(self, mock_embed, mock_index_class):
        """Test successfully adding multiple todos in batch"""
        # Arrange
        todos = [
            Todo.objects.create(
                user=self.user,
                todo_title=f"Task {i}",
                priority="MEDIUM",
                progress=i * 10
            )
            for i in range(1, 4)
        ]
        
        mock_embed.return_value = {
            "embedding": [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        }
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act
        service.add_todos_batch(todos)

        # Assert
        mock_embed.assert_called_once()
        mock_index.upsert.assert_called_once()
        
        # Verify batch upsert
        call_args = mock_index.upsert.call_args[1]["vectors"]
        self.assertEqual(len(call_args), 3)
        
        # Verify first todo in batch
        self.assertEqual(call_args[0][0], str(todos[0].id))
        self.assertEqual(call_args[0][2]["title"], "Task 1")

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_add_todos_batch_empty_list(self, mock_embed, mock_index_class):
        """Test batch add with empty list"""
        # Arrange
        mock_embed.return_value = {"embedding": []}
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act
        service.add_todos_batch([])

        # Assert
        mock_embed.assert_called_once_with(
            model="models/text-embedding-004",
            content=[],
            task_type="retrieval_document"
        )
        # Upsert should be called with empty list
        call_args = mock_index.upsert.call_args[1]["vectors"]
        self.assertEqual(len(call_args), 0)

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token",
        GOOGLE_API_KEY="test_api_key",
    )
    @patch("todos.vector_service.Index")
    @patch("todos.embedding_service.genai.embed_content")
    def test_add_todos_batch_embedding_error(self, mock_embed, mock_index_class):
        """Test batch add with embedding error"""
        # Arrange
        todos = [self.todo]
        mock_embed.side_effect = Exception("Batch Embedding Error")
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        service = VectorService()

        # Act & Assert
        with self.assertRaises(Exception) as context:
            service.add_todos_batch(todos)

        self.assertIn("Batch Embedding Error", str(context.exception))
        # Upsert should not be called if embedding fails
        mock_index.upsert.assert_not_called()