"""
Todoモデルのテスト（pytest）
データベースの制約、デフォルト値、リレーションシップを確認します。
"""
import pytest
from django.contrib.auth import get_user_model

from apps.todos.models import Todo

User = get_user_model()


@pytest.mark.django_db
class TestTodoModel:
    """Todoモデルの機能テスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    def test_create_todo(self):
        """Todoが正しくデータベースに作成されるかテスト"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=50
        )

        assert todo.todo_title == "Test Todo"
        assert todo.priority == Todo.Priority.HIGH
        assert todo.progress == 50
        assert todo.user == self.user

    def test_default_priority(self):
        """優先度が指定されない場合、デフォルトのMEDIUM（中）になるかテスト"""
        todo = Todo.objects.create(user=self.user, todo_title="Default Priority Todo")

        assert todo.priority == Todo.Priority.MEDIUM

    def test_default_progress(self):
        """進捗が指定されない場合、デフォルトの0になるかテスト"""
        todo = Todo.objects.create(user=self.user, todo_title="Default Progress Todo")

        assert todo.progress == 0

    def test_priority_choices(self):
        """優先度の定数定義（LOW, MEDIUM, HIGH）が正しいかテスト"""
        assert Todo.Priority.LOW == "LOW"
        assert Todo.Priority.MEDIUM == "MEDIUM"
        assert Todo.Priority.HIGH == "HIGH"

    def test_str_representation(self):
        """モデルを文字列評価した際（管理画面など）にタイトルを返すかテスト"""
        todo = Todo.objects.create(user=self.user, todo_title="String Test")

        assert str(todo) == "String Test"

    def test_ordering(self):
        """Todoが作成日時の降順（created_at DESC）で並んでいるかテスト"""
        todo1 = Todo.objects.create(user=self.user, todo_title="First")
        todo2 = Todo.objects.create(user=self.user, todo_title="Second")

        todos = list(Todo.objects.all())
        assert todos[0] == todo2
        assert todos[1] == todo1

    def test_user_cascade_delete(self):
        """ユーザー削除時に紐づくTodoも連鎖削除（ON DELETE CASCADE）されるかテスト"""
        todo = Todo.objects.create(user=self.user, todo_title="Test")
        todo_id = todo.id

        self.user.delete()

        assert not Todo.objects.filter(id=todo_id).exists()