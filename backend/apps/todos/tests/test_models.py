"""
Todoモデルのテスト
データベースの制約、デフォルト値、リレーションシップを確認します。
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.todos.models import Todo

User = get_user_model()

class TodoModelTestCase(TestCase):
    """Todoモデルの機能テスト"""

    def setUp(self):
        """テスト用の共通ユーザーを作成"""
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
        
        self.assertEqual(todo.todo_title, "Test Todo")
        self.assertEqual(todo.priority, Todo.Priority.HIGH)
        self.assertEqual(todo.progress, 50)
        self.assertEqual(todo.user, self.user)

    def test_default_priority(self):
        """優先度が指定されない場合、デフォルトのMEDIUM（中）になるかテスト"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Default Priority Todo"
        )
        self.assertEqual(todo.priority, Todo.Priority.MEDIUM)

    def test_default_progress(self):
        """進捗が指定されない場合、デフォルトの0になるかテスト"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Default Progress Todo"
        )
        self.assertEqual(todo.progress, 0)

    def test_priority_choices(self):
        """優先度の定数定義（LOW, MEDIUM, HIGH）が正しいかテスト"""
        self.assertEqual(Todo.Priority.LOW, 'LOW')
        self.assertEqual(Todo.Priority.MEDIUM, 'MEDIUM')
        self.assertEqual(Todo.Priority.HIGH, 'HIGH')

    def test_str_representation(self):
        """モデルを文字列評価した際（管理画面など）にタイトルを返すかテスト"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="String Test"
        )
        self.assertEqual(str(todo), "String Test")

    def test_ordering(self):
        """Todoが作成日時の降順（created_at DESC）で並んでいるかテスト"""
        todo1 = Todo.objects.create(user=self.user, todo_title="First")
        todo2 = Todo.objects.create(user=self.user, todo_title="Second")
        
        todos = list(Todo.objects.all())
        # 新しく作った方が最初に来ることを期待
        self.assertEqual(todos[0], todo2)
        self.assertEqual(todos[1], todo1)

    def test_user_cascade_delete(self):
        """ユーザー削除時に紐づくTodoも連鎖削除（ON DELETE CASCADE）されるかテスト"""
        todo = Todo.objects.create(user=self.user, todo_title="Test")
        todo_id = todo.id
        
        # ユーザーを削除
        self.user.delete()
        
        # Todoが存在しないことを確認
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())