"""
Todoアプリのシリアライザテスト
データのバリデーション、変換ロジック、読み取り専用フィールドをテストします。
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.todos.models import Todo
from apps.todos.serializers import (
    TodoSerializer,
    TodoSearchParamsSerializer,
    VectorIndexingWebhookSerializer,
)

User = get_user_model()

class TodoSerializerTestCase(TestCase):
    """メインのTodoSerializer（CRUD用）のテスト"""

    def setUp(self):
        """テスト用ユーザーの作成"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    def test_serializer_valid_data(self):
        """有効な入力データでバリデーションが通るかテスト"""
        data = {
            'todo_title': 'Test Todo',
            'priority': 'HIGH',
            'progress': 75
        }
        serializer = TodoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_title_validation_empty(self):
        """タイトルが空文字（空白のみ）の場合にエラーになるかテスト"""
        data = {
            'todo_title': '   ',
            'priority': 'MEDIUM',
            'progress': 0
        }
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('todo_title', serializer.errors)

    def test_serializer_title_validation_too_long(self):
        """タイトルが200文字を超えた場合にエラーになるかテスト"""
        data = {
            'todo_title': 'A' * 201,
            'priority': 'MEDIUM',
            'progress': 0
        }
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('todo_title', serializer.errors)

    def test_serializer_title_trimming(self):
        """タイトルの前後の余計な空白が自動でトリミングされるかテスト"""
        data = {
            'todo_title': '   Trim Me   ',
            'priority': 'MEDIUM',
            'progress': 0
        }
        serializer = TodoSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['todo_title'], 'Trim Me')

    def test_serializer_progress_validation_range(self):
        """進捗率（progress）が0未満、または100超の場合にエラーになるかテスト"""
        # 0未満
        low_data = {'todo_title': 'Test', 'progress': -1}
        low_serializer = TodoSerializer(data=low_data)
        self.assertFalse(low_serializer.is_valid())

        # 100超
        high_data = {'todo_title': 'Test', 'progress': 101}
        high_serializer = TodoSerializer(data=high_data)
        self.assertFalse(high_serializer.is_valid())

    def test_serializer_priority_validation(self):
        """定義されていない無効な優先度が指定された場合にエラーになるかテスト"""
        data = {
            'todo_title': 'Test',
            'priority': 'URGENT', # 無効な値
            'progress': 0
        }
        serializer = TodoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('priority', serializer.errors)

    def test_serializer_read_only_fields(self):
        """idやcreated_atなどが、出力には含まれるが入力（更新）はできないことをテスト"""
        todo = Todo.objects.create(user=self.user, todo_title="Test")
        serializer = TodoSerializer(todo)
        
        self.assertIn('id', serializer.data)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)


class TodoSearchParamsSerializerTestCase(TestCase):
    """ベクトル検索パラメータ用のシリアライザテスト"""

    def test_valid_search_params(self):
        """検索クエリとパラメータが正しく受理されるかテスト"""
        data = {
            'q': 'find my task',
            'top_k': 10,
            'min_score': 0.7
        }
        serializer = TodoSearchParamsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_default_values(self):
        """オプションパラメータが未指定の場合にデフォルト値が設定されるかテスト"""
        data = {'q': 'search'}
        serializer = TodoSearchParamsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # top_k=5, min_score=0.5 がデフォルトであることを期待
        self.assertEqual(serializer.validated_data['top_k'], 5)
        self.assertEqual(serializer.validated_data['min_score'], 0.5)

    def test_query_required(self):
        """検索クエリ 'q' が必須項目であることをテスト"""
        serializer = TodoSearchParamsSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('q', serializer.errors)


class VectorIndexingWebhookSerializerTestCase(TestCase):
    """Webhook動作用のシリアライザテスト"""

    def test_valid_upsert(self):
        """有効な登録（upsert）指示をテスト"""
        data = {'todo_id': 1, 'operation': 'upsert'}
        serializer = VectorIndexingWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_delete(self):
        """有効な削除（delete）指示をテスト"""
        data = {'todo_id': 1, 'operation': 'delete'}
        serializer = VectorIndexingWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_operation(self):
        """無効なオペレーション文字列を拒否するかテスト"""
        data = {'todo_id': 1, 'operation': 'update_all'} # 定義外
        serializer = VectorIndexingWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())