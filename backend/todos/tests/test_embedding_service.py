"""
Tests for EmbeddingService
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from todos.embedding_service import EmbeddingService
from todos.models import Todo

User = get_user_model()


class EmbeddingServiceTestCase(TestCase):
    """Tests for EmbeddingService"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.service = EmbeddingService()

    def test_prepare_text_basic(self):
        """Test basic text preparation"""
        # Arrange
        todo = Todo.objects.create(
            user=self.user,
            todo_title="会議資料の作成",
            priority="HIGH",
            progress=50
        )

        # Act
        text = EmbeddingService.prepare_text(todo)

        # Assert
        self.assertIn("会議資料の作成", text)
        self.assertIn("優先度:高", text)
        self.assertIn("進捗:50%", text)

    def test_prepare_text_normalization(self):
        """Test text normalization (whitespace removal)"""
        # Arrange
        todo = Todo.objects.create(
            user=self.user,
            todo_title="  Multiple   Spaces   Test  ",
            priority="MEDIUM",
            progress=0
        )

        # Act
        text = EmbeddingService.prepare_text(todo)

        # Assert
        # Multiple spaces should be normalized to single space
        self.assertNotIn("  ", text)
        # Leading/trailing spaces should be removed
        self.assertFalse(text.startswith(" "))
        self.assertFalse(text.endswith(" "))

    def test_prepare_text_all_priorities(self):
        """Test text preparation with all priority levels"""
        priorities = [
            ("HIGH", "高"),
            ("MEDIUM", "中"),
            ("LOW", "低"),
        ]

        for priority_code, priority_display in priorities:
            with self.subTest(priority=priority_code):
                # Arrange
                todo = Todo.objects.create(
                    user=self.user,
                    todo_title="Test",
                    priority=priority_code,
                    progress=0
                )

                # Act
                text = EmbeddingService.prepare_text(todo)

                # Assert
                self.assertIn(f"優先度:{priority_display}", text)

    @override_settings(GOOGLE_API_KEY="test_api_key")
    @patch("todos.embedding_service.genai.embed_content")
    def test_embed_text_success(self, mock_embed):
        """Test successful text embedding"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.1] * 768}
        text = "テストテキスト"

        # Act
        result = self.service.embed_text(text)

        # Assert
        self.assertEqual(len(result), 768)
        self.assertEqual(result[0], 0.1)
        mock_embed.assert_called_once_with(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )

    @override_settings(GOOGLE_API_KEY="test_api_key")
    @patch("todos.embedding_service.genai.embed_content")
    def test_embed_text_query_task_type(self, mock_embed):
        """Test embedding with query task type"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.2] * 768}
        text = "検索クエリ"

        # Act
        result = self.service.embed_text(text, task_type="retrieval_query")

        # Assert
        self.assertEqual(len(result), 768)
        mock_embed.assert_called_once_with(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )

    @override_settings(GOOGLE_API_KEY="test_api_key")
    @patch("todos.embedding_service.genai.embed_content")
    def test_embed_text_api_error(self, mock_embed):
        """Test embedding with API error"""
        # Arrange
        mock_embed.side_effect = Exception("API Error")
        text = "テスト"

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.service.embed_text(text)

        self.assertIn("API Error", str(context.exception))

    @override_settings(GOOGLE_API_KEY="test_api_key")
    @patch("todos.embedding_service.genai.embed_content")
    def test_embed_batch_success(self, mock_embed):
        """Test successful batch embedding"""
        # Arrange
        mock_embed.return_value = {
            "embedding": [
                [0.1] * 768,
                [0.2] * 768,
                [0.3] * 768
            ]
        }
        texts = ["テキスト1", "テキスト2", "テキスト3"]

        # Act
        result = self.service.embed_batch(texts)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0]), 768)
        self.assertEqual(result[0][0], 0.1)
        self.assertEqual(result[1][0], 0.2)
        self.assertEqual(result[2][0], 0.3)
        mock_embed.assert_called_once_with(
            model="models/text-embedding-004",
            content=texts,
            task_type="retrieval_document"
        )

    @override_settings(GOOGLE_API_KEY="test_api_key")
    @patch("todos.embedding_service.genai.embed_content")
    def test_embed_batch_empty_list(self, mock_embed):
        """Test batch embedding with empty list"""
        # Arrange
        mock_embed.return_value = {"embedding": []}
        texts = []

        # Act
        result = self.service.embed_batch(texts)

        # Assert
        self.assertEqual(len(result), 0)

    @override_settings(GOOGLE_API_KEY="test_api_key")
    @patch("todos.embedding_service.genai.embed_content")
    def test_embed_batch_api_error(self, mock_embed):
        """Test batch embedding with API error"""
        # Arrange
        mock_embed.side_effect = Exception("Batch API Error")
        texts = ["テキスト1", "テキスト2"]

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.service.embed_batch(texts)

        self.assertIn("Batch API Error", str(context.exception))

    def test_prepare_text_empty_title(self):
        """Test text preparation with empty title"""
        # Arrange
        todo = Todo.objects.create(
            user=self.user,
            todo_title="",
            priority="LOW",
            progress=100
        )

        # Act
        text = EmbeddingService.prepare_text(todo)

        # Assert
        # Should still include metadata even with empty title
        self.assertIn("優先度:低", text)
        self.assertIn("進捗:100%", text)

    def test_prepare_text_special_characters(self):
        """Test text preparation with special characters"""
        # Arrange
        todo = Todo.objects.create(
            user=self.user,
            todo_title="タスク@#$%^&*()_+-=[]{}|;:',.<>?/",
            priority="HIGH",
            progress=25
        )

        # Act
        text = EmbeddingService.prepare_text(todo)

        # Assert
        # Special characters should be preserved
        self.assertIn("@#$%^&*()_+-=[]{}|;:',.<>?/", text)