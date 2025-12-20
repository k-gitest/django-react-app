from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from todos.models import Todo

User = get_user_model()


class TodoModelTestCase(TestCase):
    """Todoモデルのテスト"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )

    def test_create_todo_with_all_fields(self):
        """Todo作成: 全フィールドを指定"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title='テストタスク',
            priority=Todo.Priority.HIGH,
            progress=50
        )
        
        self.assertEqual(todo.user, self.user)
        self.assertEqual(todo.todo_title, 'テストタスク')
        self.assertEqual(todo.priority, Todo.Priority.HIGH)
        self.assertEqual(todo.progress, 50)
        self.assertIsNotNone(todo.created_at)
        self.assertIsNotNone(todo.updated_at)

    def test_create_todo_with_default_values(self):
        """Todo作成: デフォルト値の確認"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title='デフォルトタスク'
        )
        
        self.assertEqual(todo.priority, Todo.Priority.MEDIUM)
        self.assertEqual(todo.progress, 0)

    def test_todo_str_representation(self):
        """__str__メソッド: タイトルが返される"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title='文字列表現テスト'
        )
        
        self.assertEqual(str(todo), '文字列表現テスト')

    def test_todo_ordering(self):
        """Meta.ordering: 作成日時の降順で並ぶ"""
        todo1 = Todo.objects.create(user=self.user, todo_title='古いタスク')
        todo2 = Todo.objects.create(user=self.user, todo_title='新しいタスク')
        
        todos = Todo.objects.all()
        
        self.assertEqual(todos[0], todo2)  # 新しいのが先
        self.assertEqual(todos[1], todo1)

    def test_user_cascade_delete(self):
        """ユーザー削除時: 関連するTodoも削除される"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title='削除されるタスク'
        )
        todo_id = todo.id
        
        # ユーザーを削除
        self.user.delete()
        
        # Todoも削除されていることを確認
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_related_name_todos(self):
        """related_name: user.todosでアクセス可能"""
        todo1 = Todo.objects.create(user=self.user, todo_title='タスク1')
        todo2 = Todo.objects.create(user=self.user, todo_title='タスク2')
        
        user_todos = self.user.todos.all()
        
        self.assertEqual(user_todos.count(), 2)
        self.assertIn(todo1, user_todos)
        self.assertIn(todo2, user_todos)

    def test_priority_choices(self):
        """Priority選択肢: 定義された値のみ許可"""
        # 正しい値
        for priority in [Todo.Priority.LOW, Todo.Priority.MEDIUM, Todo.Priority.HIGH]:
            todo = Todo.objects.create(
                user=self.user,
                todo_title=f'{priority}タスク',
                priority=priority
            )
            self.assertEqual(todo.priority, priority)

    def test_progress_range(self):
        """progress: 0-100の範囲で設定可能（モデルレベルの制約なし）"""
        # 正常範囲
        todo1 = Todo.objects.create(user=self.user, todo_title='0%', progress=0)
        todo2 = Todo.objects.create(user=self.user, todo_title='100%', progress=100)
        
        self.assertEqual(todo1.progress, 0)
        self.assertEqual(todo2.progress, 100)
        
        # 注意: モデルにバリデーションがないため、範囲外も保存できてしまう
        # これはSerializerやService層でバリデーションする設計

    def test_todo_title_max_length(self):
        """todo_title: 最大255文字"""
        long_title = 'あ' * 255
        todo = Todo.objects.create(
            user=self.user,
            todo_title=long_title
        )
        
        self.assertEqual(len(todo.todo_title), 255)

    def test_auto_now_fields(self):
        """created_at/updated_at: 自動設定される"""
        import time
        
        todo = Todo.objects.create(
            user=self.user,
            todo_title='時刻テスト'
        )
        created_at = todo.created_at
        updated_at = todo.updated_at
        
        # 少し待ってから更新
        time.sleep(0.1)
        todo.progress = 50
        todo.save()
        
        # created_atは変わらない、updated_atは更新される
        self.assertEqual(todo.created_at, created_at)
        self.assertGreater(todo.updated_at, updated_at)