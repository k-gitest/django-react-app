from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from todos.models import Todo

User = get_user_model()


class TodoViewSetTestCase(TestCase):
    """TodoViewSetのAPIテスト"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        self.client = APIClient()
        
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
            todo_title='User1のタスク1',
            priority=Todo.Priority.HIGH,
            progress=50
        )
        self.todo2 = Todo.objects.create(
            user=self.user1,
            todo_title='User1のタスク2',
            priority=Todo.Priority.MEDIUM,
            progress=100
        )
        self.todo3 = Todo.objects.create(
            user=self.user2,
            todo_title='User2のタスク',
            priority=Todo.Priority.LOW,
            progress=0
        )

    def test_list_todos_unauthenticated(self):
        """一覧取得: 未認証ユーザーは401"""
        response = self.client.get('/api/v1/todos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_todos_authenticated(self):
        """一覧取得: 認証済みユーザーは自分のタスクのみ取得"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/v1/todos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # 自分のタスクのみ含まれる
        titles = [todo['todo_title'] for todo in response.data]
        self.assertIn('User1のタスク1', titles)
        self.assertIn('User1のタスク2', titles)
        self.assertNotIn('User2のタスク', titles)

    def test_retrieve_todo_success(self):
        """詳細取得: 自分のタスクは取得可能"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/v1/todos/{self.todo1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['todo_title'], 'User1のタスク1')
        self.assertEqual(response.data['priority'], 'HIGH')
        self.assertEqual(response.data['progress'], 50)

    def test_retrieve_todo_unauthorized(self):
        """詳細取得: 他人のタスクは取得不可（404）"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/v1/todos/{self.todo3.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_todo_success(self):
        """作成: 正常なデータでタスクを作成"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'todo_title': '新しいタスク',
            'priority': 'HIGH',
            'progress': 0
        }
        
        response = self.client.post('/api/v1/todos/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['todo_title'], '新しいタスク')
        self.assertEqual(response.data['priority'], 'HIGH')
        
        # DBに保存されているか確認
        self.assertTrue(
            Todo.objects.filter(
                user=self.user1,
                todo_title='新しいタスク'
            ).exists()
        )

    def test_create_todo_with_default_values(self):
        """作成: 最小限のデータで作成（デフォルト値使用）"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'todo_title': 'シンプルなタスク'
        }
        
        response = self.client.post('/api/v1/todos/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['priority'], 'MEDIUM')  # デフォルト
        self.assertEqual(response.data['progress'], 0)  # デフォルト

    def test_create_todo_invalid_priority(self):
        """作成: 無効な優先度で400エラー"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'todo_title': 'テストタスク',
            'priority': 'INVALID'
        }
        
        response = self.client.post('/api/v1/todos/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_todo_missing_title(self):
        """作成: タイトルなしで400エラー"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'priority': 'HIGH'
        }
        
        response = self.client.post('/api/v1/todos/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('todo_title', response.data)

    def test_update_todo_success(self):
        """更新: 自分のタスクを更新"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'todo_title': '更新されたタスク',
            'progress': 75
        }
        
        response = self.client.patch(f'/api/v1/todos/{self.todo1.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['todo_title'], '更新されたタスク')
        self.assertEqual(response.data['progress'], 75)
        
        # DBも更新されているか確認
        self.todo1.refresh_from_db()
        self.assertEqual(self.todo1.todo_title, '更新されたタスク')
        self.assertEqual(self.todo1.progress, 75)

    def test_update_todo_partial(self):
        """更新: 部分更新が可能"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'progress': 100
        }
        
        response = self.client.patch(f'/api/v1/todos/{self.todo1.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['progress'], 100)
        self.assertEqual(response.data['todo_title'], 'User1のタスク1')  # 変更なし

    def test_update_todo_unauthorized(self):
        """更新: 他人のタスクは更新不可（404）"""
        self.client.force_authenticate(user=self.user1)
        data = {
            'progress': 100
        }
        
        response = self.client.patch(f'/api/v1/todos/{self.todo3.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_todo_success(self):
        """削除: 自分のタスクを削除"""
        self.client.force_authenticate(user=self.user1)
        todo_id = self.todo1.id
        
        response = self.client.delete(f'/api/v1/todos/{todo_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # DBから削除されているか確認
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_delete_todo_unauthorized(self):
        """削除: 他人のタスクは削除不可（404）"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.delete(f'/api/v1/todos/{self.todo3.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # DBに残っているか確認
        self.assertTrue(Todo.objects.filter(id=self.todo3.id).exists())

    def test_stats_action_success(self):
        """カスタムアクション: stats - 優先度別統計"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/v1/todos/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # データ構造の確認
        stats_dict = {item['priority']: item['count'] for item in response.data}
        self.assertEqual(stats_dict.get('HIGH', 0), 1)
        self.assertEqual(stats_dict.get('MEDIUM', 0), 1)

    def test_stats_action_unauthenticated(self):
        """カスタムアクション: stats - 未認証は401"""
        response = self.client.get('/api/v1/todos/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_progress_stats_action_success(self):
        """カスタムアクション: progress-stats - 進捗率別統計"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/v1/todos/progress-stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        
        # 必要なキーが含まれているか確認
        expected_keys = ['range_0_20', 'range_21_40', 'range_41_60', 
                        'range_61_80', 'range_81_100']
        for key in expected_keys:
            self.assertIn(key, response.data)
        
        # 実際の値を確認
        self.assertEqual(response.data['range_41_60'], 1)  # progress=50
        self.assertEqual(response.data['range_81_100'], 1)  # progress=100

    def test_progress_stats_action_unauthenticated(self):
        """カスタムアクション: progress-stats - 未認証は401"""
        response = self.client.get('/api/v1/todos/progress-stats/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_isolation(self):
        """ユーザー分離: 各ユーザーは自分のデータのみアクセス可能"""
        # User1でログイン
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get('/api/v1/todos/')
        user1_count = len(response1.data)
        
        # User2でログイン
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get('/api/v1/todos/')
        user2_count = len(response2.data)
        
        # それぞれのタスク数が正しい
        self.assertEqual(user1_count, 2)
        self.assertEqual(user2_count, 1)