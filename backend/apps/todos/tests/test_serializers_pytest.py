"""
Todoアプリのシリアライザテスト（pytest）
データのバリデーション、変換ロジック、読み取り専用フィールドをテストします。
"""
import pytest
from django.contrib.auth import get_user_model

from apps.todos.models import Todo
from apps.todos.serializers import (
    TodoSearchParamsSerializer,
    TodoSerializer,
    VectorIndexingWebhookSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestTodoSerializer:
    """メインのTodoSerializer（CRUD用）のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    def test_serializer_valid_data(self):
        """有効な入力データでバリデーションが通るかテスト"""
        data = {
            "todo_title": "Test Todo",
            "priority": "HIGH",
            "progress": 75
        }

        serializer = TodoSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_title_validation_empty(self):
        """タイトルが空文字（空白のみ）の場合にエラーになるかテスト"""
        data = {
            "todo_title": "   ",
            "priority": "MEDIUM",
            "progress": 0
        }

        serializer = TodoSerializer(data=data)
        assert not serializer.is_valid()
        assert "todo_title" in serializer.errors

    def test_serializer_title_validation_too_long(self):
        """タイトルが200文字を超えた場合にエラーになるかテスト"""
        data = {
            "todo_title": "A" * 201,
            "priority": "MEDIUM",
            "progress": 0
        }

        serializer = TodoSerializer(data=data)
        assert not serializer.is_valid()
        assert "todo_title" in serializer.errors

    def test_serializer_title_trimming(self):
        """タイトルの前後の余計な空白が自動でトリミングされるかテスト"""
        data = {
            "todo_title": "   Trim Me   ",
            "priority": "MEDIUM",
            "progress": 0
        }

        serializer = TodoSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["todo_title"] == "Trim Me"

    def test_serializer_progress_validation_range(self):
        """進捗率（progress）が0未満、または100超の場合にエラーになるかテスト"""
        low_serializer = TodoSerializer(data={"todo_title": "Test", "progress": -1})
        assert not low_serializer.is_valid()

        high_serializer = TodoSerializer(data={"todo_title": "Test", "progress": 101})
        assert not high_serializer.is_valid()

    def test_serializer_priority_validation(self):
        """定義されていない無効な優先度が指定された場合にエラーになるかテスト"""
        data = {
            "todo_title": "Test",
            "priority": "URGENT",  # 無効な値
            "progress": 0
        }

        serializer = TodoSerializer(data=data)
        assert not serializer.is_valid()
        assert "priority" in serializer.errors

    def test_serializer_read_only_fields(self):
        """idやcreated_atなどが、出力には含まれるが入力（更新）はできないことをテスト"""
        todo = Todo.objects.create(user=self.user, todo_title="Test")

        serializer = TodoSerializer(todo)
        assert "id" in serializer.data
        assert "created_at" in serializer.data
        assert "updated_at" in serializer.data


@pytest.mark.django_db
class TestTodoSearchParamsSerializer:
    """ベクトル検索パラメータ用のシリアライザテスト"""

    def test_valid_search_params(self):
        """検索クエリとパラメータが正しく受理されるかテスト"""
        data = {
            "q": "find my task",
            "top_k": 10,
            "min_score": 0.7
        }

        serializer = TodoSearchParamsSerializer(data=data)
        assert serializer.is_valid()

    def test_default_values(self):
        """オプションパラメータが未指定の場合にデフォルト値が設定されるかテスト"""
        serializer = TodoSearchParamsSerializer(data={"q": "search"})

        assert serializer.is_valid()
        assert serializer.validated_data["top_k"] == 5
        assert serializer.validated_data["min_score"] == 0.5

    def test_query_required(self):
        """検索クエリ 'q' が必須項目であることをテスト"""
        serializer = TodoSearchParamsSerializer(data={})

        assert not serializer.is_valid()
        assert "q" in serializer.errors


@pytest.mark.django_db
class TestVectorIndexingWebhookSerializer:
    """Webhook動作用のシリアライザテスト"""

    def test_valid_upsert(self):
        """有効な登録（upsert）指示をテスト"""
        serializer = VectorIndexingWebhookSerializer(
            data={"todo_id": 1, "operation": "upsert"}
        )
        assert serializer.is_valid()

    def test_valid_delete(self):
        """有効な削除（delete）指示をテスト"""
        serializer = VectorIndexingWebhookSerializer(
            data={"todo_id": 1, "operation": "delete"}
        )
        assert serializer.is_valid()

    def test_invalid_operation(self):
        """無効なオペレーション文字列を拒否するかテスト"""
        serializer = VectorIndexingWebhookSerializer(
            data={"todo_id": 1, "operation": "update_all"}  # 定義外
        )
        assert not serializer.is_valid()