from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from todos.models import Todo
from todos.serializers import TodoSerializer

User = get_user_model()


class TodoSerializerTestCase(TestCase):
    """TodoSerializerのテスト"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title='テストタスク',
            priority=Todo.Priority.MEDIUM,
            progress=50
        )

    # ============================================
    # シリアライズ（Model → JSON）のテスト
    # ============================================

    def test_serialize_todo(self):
        """シリアライズ: Todoオブジェクトを正しくJSONに変換"""
        serializer = TodoSerializer(self.todo)
        data = serializer.data
        
        self.assertEqual(data['id'], self.todo.id)
        self.assertEqual(data['user'], self.user.email)
        self.assertEqual(data['todo_title'], 'テストタスク')
        self.assertEqual(data['priority'], 'MEDIUM')
        self.assertEqual(data['progress'], 50)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_serialize_multiple_todos(self):
        """シリアライズ: 複数のTodoを変換"""
        todo2 = Todo.objects.create(
            user=self.user,
            todo_title='タスク2',
            priority=Todo.Priority.HIGH
        )
        
        serializer = TodoSerializer([self.todo, todo2], many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['todo_title'], 'テストタスク')
        self.assertEqual(data[1]['todo_title'], 'タスク2')

    # ============================================
    # デシリアライズ（JSON → Model）のテスト
    # ============================================

    def test_deserialize_valid_data(self):
        """デシリアライズ: 正常なデータの検証"""
        data = {
            'todo_title': '新しいタスク',
            'priority': 'HIGH',
            'progress': 75
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['todo_title'], '新しいタスク')
        self.assertEqual(serializer.validated_data['priority'], 'HIGH')
        self.assertEqual(serializer.validated_data['progress'], 75)

    def test_deserialize_minimal_data(self):
        """デシリアライズ: 最小限のデータ（タイトルのみ）"""
        data = {
            'todo_title': 'シンプルなタスク'
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['todo_title'], 'シンプルなタスク')

    # ============================================
    # validate_todo_title のテスト
    # ============================================

    def test_validate_todo_title_empty_string(self):
        """バリデーション: 空文字列のタイトルはエラー"""
        data = {
            'todo_title': ''
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('todo_title', serializer.errors)
        # DRFの自動バリデーションメッセージ
        self.assertIn('blank', str(serializer.errors['todo_title'][0].code))

    def test_validate_todo_title_whitespace_only(self):
        """バリデーション: 空白のみのタイトルはエラー"""
        data = {
            'todo_title': '   '
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('todo_title', serializer.errors)

    def test_validate_todo_title_trims_whitespace(self):
        """バリデーション: タイトルの前後空白をトリミング"""
        data = {
            'todo_title': '  タイトル  '
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['todo_title'], 'タイトル')

    def test_validate_todo_title_too_long(self):
        """バリデーション: 255文字を超えるタイトルはエラー"""
        data = {
            'todo_title': 'あ' * 256
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('todo_title', serializer.errors)
        # DRFの自動バリデーションメッセージ
        self.assertIn('max_length', str(serializer.errors['todo_title'][0].code))

    def test_validate_todo_title_exactly_255_chars(self):
        """バリデーション: 255文字ちょうどは許可"""
        data = {
            'todo_title': 'あ' * 255
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['todo_title']), 255)

    # ============================================
    # validate_progress のテスト
    # ============================================

    def test_validate_progress_valid_values(self):
        """バリデーション: 0-100の範囲は許可"""
        for progress in [0, 50, 100]:
            data = {
                'todo_title': 'テスト',
                'progress': progress
            }
            
            serializer = TodoSerializer(data=data)
            
            self.assertTrue(serializer.is_valid(), f"progress={progress} should be valid")
            self.assertEqual(serializer.validated_data['progress'], progress)

    def test_validate_progress_negative(self):
        """バリデーション: 負の進捗率はエラー"""
        data = {
            'todo_title': 'テスト',
            'progress': -1
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('progress', serializer.errors)
        self.assertIn('0から100の範囲', str(serializer.errors['progress']))

    def test_validate_progress_over_100(self):
        """バリデーション: 100を超える進捗率はエラー"""
        data = {
            'todo_title': 'テスト',
            'progress': 101
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('progress', serializer.errors)
        self.assertIn('0から100の範囲', str(serializer.errors['progress']))

    def test_validate_progress_not_integer(self):
        """バリデーション: 整数以外の進捗率はエラー"""
        data = {
            'todo_title': 'テスト',
            'progress': 'invalid'
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('progress', serializer.errors)

    def test_validate_progress_float(self):
        """バリデーション: 浮動小数点数はエラー"""
        data = {
            'todo_title': 'テスト',
            'progress': 50.5
        }
        
        serializer = TodoSerializer(data=data)
        
        # DRFは自動的に整数に変換しようとするが、
        # validate_progressでisinstance(value, int)をチェックしている
        self.assertFalse(serializer.is_valid())

    # ============================================
    # priority のバリデーション（ModelSerializerの自動検証）
    # ============================================

    def test_validate_priority_valid_choices(self):
        """バリデーション: 有効な優先度は許可"""
        for priority in ['LOW', 'MEDIUM', 'HIGH']:
            data = {
                'todo_title': 'テスト',
                'priority': priority
            }
            
            serializer = TodoSerializer(data=data)
            
            self.assertTrue(serializer.is_valid(), f"priority={priority} should be valid")

    def test_validate_priority_invalid_choice(self):
        """バリデーション: 無効な優先度はエラー（ModelSerializerの自動検証）"""
        data = {
            'todo_title': 'テスト',
            'priority': 'INVALID'
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('priority', serializer.errors)

    # ============================================
    # read_only_fields のテスト
    # ============================================

    def test_read_only_fields_ignored_on_create(self):
        """read_only_fields: 作成時は無視される"""
        data = {
            'todo_title': 'テスト',
            'id': 999,  # ← 無視されるべき
            'user': 'hacker@example.com',  # ← 無視されるべき
            'created_at': '2020-01-01T00:00:00Z',  # ← 無視されるべき
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        # read_only_fieldsはvalidated_dataに含まれない
        self.assertNotIn('id', serializer.validated_data)
        self.assertNotIn('user', serializer.validated_data)
        self.assertNotIn('created_at', serializer.validated_data)

    def test_update_existing_todo(self):
        """更新: 既存Todoの更新"""
        data = {
            'todo_title': '更新されたタイトル',
            'progress': 100
        }
        
        serializer = TodoSerializer(self.todo, data=data, partial=True)
        
        self.assertTrue(serializer.is_valid())
        updated_todo = serializer.save()
        
        self.assertEqual(updated_todo.todo_title, '更新されたタイトル')
        self.assertEqual(updated_todo.progress, 100)
        self.assertEqual(updated_todo.priority, 'MEDIUM')  # 変更なし

    # ============================================
    # 複合的なテスト
    # ============================================

    def test_multiple_validation_errors(self):
        """バリデーション: 複数のエラーを同時に検出"""
        data = {
            'todo_title': '',  # エラー
            'priority': 'INVALID',  # エラー
            'progress': 150  # エラー
        }
        
        serializer = TodoSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        # 3つのフィールド全てにエラーがある
        self.assertIn('todo_title', serializer.errors)
        self.assertIn('priority', serializer.errors)
        self.assertIn('progress', serializer.errors)