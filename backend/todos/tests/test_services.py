from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import Http404
from todos.models import Todo
from todos.service import TodoService

User = get_user_model()


class TodoServiceTestCase(TestCase):
    """TodoServiceのテスト"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        # テストユーザー作成
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )

        # テストデータ作成
        self.todo1 = Todo.objects.create(
            user=self.user1,
            todo_title='タスク1',
            priority=Todo.Priority.HIGH,
            progress=50
        )
        self.todo2 = Todo.objects.create(
            user=self.user1,
            todo_title='タスク2',
            priority=Todo.Priority.MEDIUM,
            progress=100
        )
        self.todo3 = Todo.objects.create(
            user=self.user2,
            todo_title='User2のタスク',
            priority=Todo.Priority.LOW,
            progress=0
        )

    # ============================================
    # get_user_todos のテスト
    # ============================================
    
    def test_get_user_todos_returns_only_user_todos(self):
        """get_user_todos: ユーザー自身のタスクのみを取得"""
        todos = TodoService.get_user_todos(self.user1)
        
        self.assertEqual(todos.count(), 2)
        self.assertIn(self.todo1, todos)
        self.assertIn(self.todo2, todos)
        self.assertNotIn(self.todo3, todos)

    def test_get_user_todos_empty_for_new_user(self):
        """get_user_todos: タスクを持たないユーザーは空のクエリセットを返す"""
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        todos = TodoService.get_user_todos(new_user)
        
        self.assertEqual(todos.count(), 0)

    # ============================================
    # create_todo のテスト
    # ============================================
    
    def test_create_todo_success(self):
        """create_todo: タスクの作成が成功する"""
        validated_data = {
            'todo_title': '新しいタスク',
            'priority': Todo.Priority.HIGH,
            'progress': 0
        }
        
        todo = TodoService.create_todo(self.user1, validated_data)
        
        self.assertIsNotNone(todo.id)
        self.assertEqual(todo.user, self.user1)
        self.assertEqual(todo.todo_title, '新しいタスク')
        self.assertEqual(todo.priority, Todo.Priority.HIGH)
        self.assertEqual(todo.progress, 0)

    def test_create_todo_with_minimal_data(self):
        """create_todo: 最小限のデータでタスクを作成"""
        validated_data = {
            'todo_title': 'シンプルなタスク',
        }
        
        todo = TodoService.create_todo(self.user1, validated_data)
        
        self.assertEqual(todo.todo_title, 'シンプルなタスク')
        self.assertEqual(todo.priority, Todo.Priority.MEDIUM)  # デフォルト
        self.assertEqual(todo.progress, 0)  # デフォルト

    # ============================================
    # update_todo のテスト
    # ============================================
    
    def test_update_todo_success(self):
        """update_todo: タスクの更新が成功する"""
        validated_data = {
            'todo_title': '更新されたタスク',
            'progress': 75
        }
        
        updated_todo = TodoService.update_todo(
            self.todo1.id,
            self.user1,
            validated_data
        )
        
        self.assertEqual(updated_todo.todo_title, '更新されたタスク')
        self.assertEqual(updated_todo.progress, 75)
        # 更新されていない項目はそのまま
        self.assertEqual(updated_todo.priority, Todo.Priority.HIGH)

    def test_update_todo_partial_update(self):
        """update_todo: 部分的な更新が可能"""
        validated_data = {'progress': 100}
        
        updated_todo = TodoService.update_todo(
            self.todo1.id,
            self.user1,
            validated_data
        )
        
        self.assertEqual(updated_todo.progress, 100)
        self.assertEqual(updated_todo.todo_title, 'タスク1')  # 変更なし

    def test_update_todo_not_found(self):
        """update_todo: 存在しないタスクの更新は404"""
        validated_data = {'progress': 100}
        
        with self.assertRaises(Http404):
            TodoService.update_todo(99999, self.user1, validated_data)

    def test_update_todo_unauthorized_user(self):
        """update_todo: 他人のタスクは更新できない（404）"""
        validated_data = {'progress': 100}
        
        # user2がuser1のタスクを更新しようとする
        with self.assertRaises(Http404):
            TodoService.update_todo(self.todo1.id, self.user2, validated_data)

    def test_update_todo_multiple_fields(self):
        """update_todo: 複数フィールドの同時更新"""
        validated_data = {
            'todo_title': '完全に更新',
            'priority': Todo.Priority.LOW,
            'progress': 100
        }
        
        updated_todo = TodoService.update_todo(
            self.todo1.id,
            self.user1,
            validated_data
        )
        
        self.assertEqual(updated_todo.todo_title, '完全に更新')
        self.assertEqual(updated_todo.priority, Todo.Priority.LOW)
        self.assertEqual(updated_todo.progress, 100)

    # ============================================
    # delete_todo のテスト
    # ============================================
    
    def test_delete_todo_success(self):
        """delete_todo: タスクの削除が成功する"""
        todo_id = self.todo1.id
        
        TodoService.delete_todo(todo_id, self.user1)
        
        # 削除されたことを確認
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_delete_todo_not_found(self):
        """delete_todo: 存在しないタスクの削除は404"""
        with self.assertRaises(Http404):
            TodoService.delete_todo(99999, self.user1)

    def test_delete_todo_unauthorized_user(self):
        """delete_todo: 他人のタスクは削除できない（404）"""
        # user2がuser1のタスクを削除しようとする
        with self.assertRaises(Http404):
            TodoService.delete_todo(self.todo1.id, self.user2)

    def test_delete_todo_does_not_affect_other_users(self):
        """delete_todo: 削除は他ユーザーのデータに影響しない"""
        user1_count_before = Todo.objects.filter(user=self.user1).count()
        user2_count_before = Todo.objects.filter(user=self.user2).count()
        
        # user2のタスクを削除
        TodoService.delete_todo(self.todo3.id, self.user2)
        
        # user1のタスク数は変わらない
        self.assertEqual(Todo.objects.filter(user=self.user1).count(), user1_count_before)
        # user2のタスクが1つ減る
        self.assertEqual(Todo.objects.filter(user=self.user2).count(), user2_count_before - 1)

    # ============================================
    # get_progress_stats のテスト
    # ============================================
    
    def test_get_progress_stats(self):
        """get_progress_stats: 進捗率の統計を正しく集計"""
        # テストデータ追加
        Todo.objects.create(user=self.user1, todo_title='タスク3', progress=10)
        Todo.objects.create(user=self.user1, todo_title='タスク4', progress=35)
        Todo.objects.create(user=self.user1, todo_title='タスク5', progress=55)
        Todo.objects.create(user=self.user1, todo_title='タスク6', progress=70)
        Todo.objects.create(user=self.user1, todo_title='タスク7', progress=95)
        
        stats = TodoService.get_progress_stats(self.user1)
        
        # 各範囲のカウントを確認
        self.assertEqual(stats['range_0_20'], 1)    # progress=10
        self.assertEqual(stats['range_21_40'], 1)   # progress=35
        self.assertEqual(stats['range_41_60'], 2)   # progress=50, 55
        self.assertEqual(stats['range_61_80'], 1)   # progress=70
        self.assertEqual(stats['range_81_100'], 2)  # progress=95, 100

    def test_get_progress_stats_empty(self):
        """get_progress_stats: タスクがない場合は全て0"""
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        
        stats = TodoService.get_progress_stats(new_user)
        
        self.assertEqual(stats['range_0_20'], 0)
        self.assertEqual(stats['range_21_40'], 0)
        self.assertEqual(stats['range_41_60'], 0)
        self.assertEqual(stats['range_61_80'], 0)
        self.assertEqual(stats['range_81_100'], 0)

    def test_get_progress_stats_only_own_todos(self):
        """get_progress_stats: 自分のタスクのみ集計される"""
        # user1のタスク: progress=50, 100
        # user2のタスク: progress=0（これは集計されない）
        
        stats = TodoService.get_progress_stats(self.user1)
        
        # user1のタスクのみカウント
        self.assertEqual(stats['range_0_20'], 0)
        self.assertEqual(stats['range_41_60'], 1)   # progress=50
        self.assertEqual(stats['range_81_100'], 1)  # progress=100

    # ============================================
    # get_priority_stats のテスト
    # ============================================
    
    def test_get_priority_stats(self):
        """get_priority_stats: 優先度別の統計を正しく集計"""
        # テストデータ追加
        Todo.objects.create(user=self.user1, todo_title='タスク3', priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user1, todo_title='タスク4', priority=Todo.Priority.LOW)
        
        stats = TodoService.get_priority_stats(self.user1)
        
        # リストをdict形式に変換して検証しやすくする
        stats_dict = {item['priority']: item['count'] for item in stats}
        
        self.assertEqual(stats_dict['HIGH'], 2)    # todo1 + 新規
        self.assertEqual(stats_dict['MEDIUM'], 1)  # todo2
        self.assertEqual(stats_dict['LOW'], 1)     # 新規

    def test_get_priority_stats_only_own_todos(self):
        """get_priority_stats: 自分のタスクのみ集計される"""
        stats = TodoService.get_priority_stats(self.user1)
        
        # user1のタスクのみ集計（user2のLOWタスクは含まれない）
        stats_dict = {item['priority']: item['count'] for item in stats}
        
        self.assertEqual(stats_dict.get('HIGH', 0), 1)
        self.assertEqual(stats_dict.get('MEDIUM', 0), 1)
        self.assertEqual(stats_dict.get('LOW', 0), 0)  # user2のタスク

    def test_get_priority_stats_empty(self):
        """get_priority_stats: タスクがない場合は空のリストを返す"""
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        
        stats = TodoService.get_priority_stats(new_user)
        
        self.assertEqual(len(stats), 0)

    def test_get_priority_stats_all_same_priority(self):
        """get_priority_stats: 全て同じ優先度の場合"""
        # 全てHIGHのタスクを作成
        Todo.objects.create(user=self.user1, todo_title='タスク3', priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user1, todo_title='タスク4', priority=Todo.Priority.HIGH)
        
        stats = TodoService.get_priority_stats(self.user1)
        stats_dict = {item['priority']: item['count'] for item in stats}
        
        # HIGHが3つ、他は集計されない
        self.assertEqual(stats_dict.get('HIGH', 0), 3)
        self.assertNotIn('LOW', stats_dict)