from apps.todos.models import Todo
from apps.todos.service import TodoService
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import Http404
from django.test import TestCase

User = get_user_model()


class TodoServiceTestCase(TestCase):
    """TodoServiceのテスト"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        # キャッシュをクリア
        cache.clear()

        # テストユーザー作成
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com", password="testpass123"
        )

        # テストデータ作成
        self.todo1 = Todo.objects.create(
            user=self.user1,
            todo_title="タスク1",
            priority=Todo.Priority.HIGH,
            progress=50,
        )
        self.todo2 = Todo.objects.create(
            user=self.user1,
            todo_title="タスク2",
            priority=Todo.Priority.MEDIUM,
            progress=100,
        )
        self.todo3 = Todo.objects.create(
            user=self.user2,
            todo_title="User2のタスク",
            priority=Todo.Priority.LOW,
            progress=0,
        )

    def tearDown(self):
        """各テスト後にキャッシュをクリア"""
        cache.clear()

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
            email="newuser@example.com", password="testpass123"
        )
        todos = TodoService.get_user_todos(new_user)

        self.assertEqual(todos.count(), 0)

    # ============================================
    # create_todo のテスト
    # ============================================

    def test_create_todo_success(self):
        """create_todo: タスクの作成が成功する"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            validated_data = {
                "todo_title": "新しいタスク",
                "priority": Todo.Priority.HIGH,
                "progress": 0,
            }

            todo = TodoService.create_todo(self.user1, validated_data)

            self.assertIsNotNone(todo.id)
            self.assertEqual(todo.user, self.user1)
            self.assertEqual(todo.todo_title, "新しいタスク")
            self.assertEqual(todo.priority, Todo.Priority.HIGH)
            self.assertEqual(todo.progress, 0)

    def test_create_todo_with_minimal_data(self):
        """create_todo: 最小限のデータでタスクを作成"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            validated_data = {
                "todo_title": "シンプルなタスク",
            }

            todo = TodoService.create_todo(self.user1, validated_data)

            self.assertEqual(todo.todo_title, "シンプルなタスク")
            self.assertEqual(todo.priority, Todo.Priority.MEDIUM)  # デフォルト
            self.assertEqual(todo.progress, 0)  # デフォルト

    # ============================================
    # update_todo のテスト
    # ============================================

    def test_update_todo_success(self):
        """update_todo: タスクの更新が成功する"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            validated_data = {"todo_title": "更新されたタスク", "progress": 75}

            updated_todo = TodoService.update_todo(
                self.todo1.id, self.user1, validated_data
            )

            self.assertEqual(updated_todo.todo_title, "更新されたタスク")
            self.assertEqual(updated_todo.progress, 75)
            # 更新されていない項目はそのまま
            self.assertEqual(updated_todo.priority, Todo.Priority.HIGH)

    def test_update_todo_partial_update(self):
        """update_todo: 部分的な更新が可能"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            validated_data = {"progress": 100}

            updated_todo = TodoService.update_todo(
                self.todo1.id, self.user1, validated_data
            )

            self.assertEqual(updated_todo.progress, 100)
            self.assertEqual(updated_todo.todo_title, "タスク1")  # 変更なし

    def test_update_todo_not_found(self):
        """update_todo: 存在しないタスクの更新は404"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            validated_data = {"progress": 100}

            with self.assertRaises(Http404):
                TodoService.update_todo(99999, self.user1, validated_data)

    def test_update_todo_unauthorized_user(self):
        """update_todo: 他人のタスクは更新できない（404）"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            validated_data = {"progress": 100}

            # user2がuser1のタスクを更新しようとする
            with self.assertRaises(Http404):
                TodoService.update_todo(self.todo1.id, self.user2, validated_data)

    def test_update_todo_multiple_fields(self):
        """update_todo: 複数フィールドの同時更新"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            validated_data = {
                "todo_title": "完全に更新",
                "priority": Todo.Priority.LOW,
                "progress": 100,
            }

            updated_todo = TodoService.update_todo(
                self.todo1.id, self.user1, validated_data
            )

            self.assertEqual(updated_todo.todo_title, "完全に更新")
            self.assertEqual(updated_todo.priority, Todo.Priority.LOW)
            self.assertEqual(updated_todo.progress, 100)

    # ============================================
    # delete_todo のテスト
    # ============================================

    def test_delete_todo_success(self):
        """delete_todo: タスクの削除が成功する"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            todo_id = self.todo1.id

            TodoService.delete_todo(todo_id, self.user1)

            # 削除されたことを確認
            self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_delete_todo_not_found(self):
        """delete_todo: 存在しないタスクの削除は404"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            with self.assertRaises(Http404):
                TodoService.delete_todo(99999, self.user1)

    def test_delete_todo_unauthorized_user(self):
        """delete_todo: 他人のタスクは削除できない（404）"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            # user2がuser1のタスクを削除しようとする
            with self.assertRaises(Http404):
                TodoService.delete_todo(self.todo1.id, self.user2)

    def test_delete_todo_does_not_affect_other_users(self):
        """delete_todo: 削除は他ユーザーのデータに影響しない"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            user1_count_before = Todo.objects.filter(user=self.user1).count()
            user2_count_before = Todo.objects.filter(user=self.user2).count()

            # user2のタスクを削除
            TodoService.delete_todo(self.todo3.id, self.user2)

            # user1のタスク数は変わらない
            self.assertEqual(
                Todo.objects.filter(user=self.user1).count(), user1_count_before
            )
            # user2のタスクが1つ減る
            self.assertEqual(
                Todo.objects.filter(user=self.user2).count(), user2_count_before - 1
            )

    # ============================================
    # get_progress_stats のテスト
    # ============================================

    def test_get_progress_stats(self):
        """get_progress_stats: 進捗率の統計を正しく集計"""
        # テストデータ追加
        Todo.objects.create(user=self.user1, todo_title="タスク3", progress=10)
        Todo.objects.create(user=self.user1, todo_title="タスク4", progress=35)
        Todo.objects.create(user=self.user1, todo_title="タスク5", progress=55)
        Todo.objects.create(user=self.user1, todo_title="タスク6", progress=70)
        Todo.objects.create(user=self.user1, todo_title="タスク7", progress=95)

        stats = TodoService.get_progress_stats(self.user1)

        # 各範囲のカウントを確認
        self.assertEqual(stats["range_0_20"], 1)  # progress=10
        self.assertEqual(stats["range_21_40"], 1)  # progress=35
        self.assertEqual(stats["range_41_60"], 2)  # progress=50, 55
        self.assertEqual(stats["range_61_80"], 1)  # progress=70
        self.assertEqual(stats["range_81_100"], 2)  # progress=95, 100

    def test_get_progress_stats_empty(self):
        """get_progress_stats: タスクがない場合は全て0"""
        new_user = User.objects.create_user(
            email="newuser@example.com", password="testpass123"
        )

        stats = TodoService.get_progress_stats(new_user)

        self.assertEqual(stats["range_0_20"], 0)
        self.assertEqual(stats["range_21_40"], 0)
        self.assertEqual(stats["range_41_60"], 0)
        self.assertEqual(stats["range_61_80"], 0)
        self.assertEqual(stats["range_81_100"], 0)

    def test_get_progress_stats_only_own_todos(self):
        """get_progress_stats: 自分のタスクのみ集計される"""
        # user1のタスク: progress=50, 100
        # user2のタスク: progress=0（これは集計されない）

        stats = TodoService.get_progress_stats(self.user1)

        # user1のタスクのみカウント
        self.assertEqual(stats["range_0_20"], 0)
        self.assertEqual(stats["range_41_60"], 1)  # progress=50
        self.assertEqual(stats["range_81_100"], 1)  # progress=100

    # ============================================
    # get_priority_stats のテスト
    # ============================================

    def test_get_priority_stats(self):
        """get_priority_stats: 優先度別の統計を正しく集計"""
        # テストデータ追加
        Todo.objects.create(
            user=self.user1, todo_title="タスク3", priority=Todo.Priority.HIGH
        )
        Todo.objects.create(
            user=self.user1, todo_title="タスク4", priority=Todo.Priority.LOW
        )

        stats = TodoService.get_priority_stats(self.user1)

        # リストをdict形式に変換して検証しやすくする
        stats_dict = {item["priority"]: item["count"] for item in stats}

        self.assertEqual(stats_dict["HIGH"], 2)  # todo1 + 新規
        self.assertEqual(stats_dict["MEDIUM"], 1)  # todo2
        self.assertEqual(stats_dict["LOW"], 1)  # 新規

    def test_get_priority_stats_only_own_todos(self):
        """get_priority_stats: 自分のタスクのみ集計される"""
        stats = TodoService.get_priority_stats(self.user1)

        # user1のタスクのみ集計（user2のLOWタスクは含まれない）
        stats_dict = {item["priority"]: item["count"] for item in stats}

        self.assertEqual(stats_dict.get("HIGH", 0), 1)
        self.assertEqual(stats_dict.get("MEDIUM", 0), 1)
        self.assertEqual(stats_dict.get("LOW", 0), 0)  # user2のタスク

    def test_get_priority_stats_empty(self):
        """get_priority_stats: タスクがない場合は空のリストを返す"""
        new_user = User.objects.create_user(
            email="newuser@example.com", password="testpass123"
        )

        stats = TodoService.get_priority_stats(new_user)

        self.assertEqual(len(stats), 0)

    def test_get_priority_stats_all_same_priority(self):
        """get_priority_stats: 全て同じ優先度の場合"""
        # 全てHIGHのタスクを作成
        Todo.objects.create(
            user=self.user1, todo_title="タスク3", priority=Todo.Priority.HIGH
        )
        Todo.objects.create(
            user=self.user1, todo_title="タスク4", priority=Todo.Priority.HIGH
        )

        stats = TodoService.get_priority_stats(self.user1)
        stats_dict = {item["priority"]: item["count"] for item in stats}

        # HIGHが3つ、他は集計されない
        self.assertEqual(stats_dict.get("HIGH", 0), 3)
        self.assertNotIn("LOW", stats_dict)

    # ============================================
    # search_similar_todos のテスト
    # ============================================

    def test_search_similar_todos_success(self):
        """search_similar_todos: セマンティック検索が正常に動作"""
        from unittest.mock import MagicMock, patch

        # VectorService.search_similar をモック
        with patch(
            "apps.todos.vector_service.VectorService"
        ) as mock_vector_service_class:
            mock_instance = MagicMock()
            mock_instance.search_similar.return_value = [
                {
                    "id": 1,
                    "score": 0.85,
                    "title": "会議資料の作成",
                    "priority": "HIGH",
                    "progress": 50,
                }
            ]
            mock_vector_service_class.return_value = mock_instance

            # Act
            results = TodoService.search_similar_todos(
                self.user1, "明日の会議", top_k=5, min_score=0.5
            )

            # Assert
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["id"], 1)
            self.assertEqual(results[0]["score"], 0.85)
            self.assertEqual(results[0]["title"], "会議資料の作成")

            # search_similar が正しいパラメータで呼ばれたか確認
            mock_instance.search_similar.assert_called_once_with(
                "明日の会議", self.user1.id, 5, 0.5
            )

    def test_search_similar_todos_empty_results(self):
        """search_similar_todos: 検索結果がない場合は空リストを返す"""
        from unittest.mock import MagicMock, patch

        with patch(
            "apps.todos.vector_service.VectorService"
        ) as mock_vector_service_class:
            mock_instance = MagicMock()
            mock_instance.search_similar.return_value = []
            mock_vector_service_class.return_value = mock_instance

            # Act
            results = TodoService.search_similar_todos(
                self.user1, "存在しないタスク", top_k=5
            )

            # Assert
            self.assertEqual(len(results), 0)

    def test_search_similar_todos_error_returns_empty_list(self):
        """search_similar_todos: エラー時は空リストを返す"""
        from unittest.mock import MagicMock, patch

        with patch(
            "apps.todos.vector_service.VectorService"
        ) as mock_vector_service_class:
            mock_instance = MagicMock()
            mock_instance.search_similar.side_effect = Exception("Vector search error")
            mock_vector_service_class.return_value = mock_instance

            # Act
            results = TodoService.search_similar_todos(self.user1, "テスト", top_k=5)

            # Assert - エラー時は空リストを返す
            self.assertEqual(len(results), 0)

    # ============================================
    # bulk_index_todos のテスト
    # ============================================

    def test_bulk_index_todos_success(self):
        """bulk_index_todos: 一括インデックスが正常にキューイングされる"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_bulk_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_bulk_123",
                "error": None,
            }

            # Act
            result = TodoService.bulk_index_todos(self.user1)

            # Assert
            self.assertTrue(result)
            mock_queue.assert_called_once_with(self.user1.id)

    def test_bulk_index_todos_qstash_failure(self):
        """bulk_index_todos: QStashキューイング失敗時はFalseを返す"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_bulk_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": False,
                "message_id": None,
                "error": "Network error",
            }

            # Act
            result = TodoService.bulk_index_todos(self.user1)

            # Assert
            self.assertFalse(result)

    def test_bulk_index_todos_exception(self):
        """bulk_index_todos: 例外発生時は例外を再送出"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_bulk_vector_indexing"
        ) as mock_queue:
            mock_queue.side_effect = Exception("Unexpected error")

            # Act & Assert
            with self.assertRaises(Exception) as context:
                TodoService.bulk_index_todos(self.user1)

            self.assertIn("Unexpected error", str(context.exception))

    # ============================================
    # ベクトル検索統合テスト（QStash キューイング）
    # ============================================

    def test_create_todo_queues_vector_indexing(self):
        """create_todo: Todo作成時にベクトルインデックスがキューイングされる"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_create_123",
                "error": None,
            }

            validated_data = {
                "todo_title": "新しいタスク",
                "priority": Todo.Priority.HIGH,
                "progress": 0,
            }

            # Act
            todo = TodoService.create_todo(self.user1, validated_data)

            # Assert
            self.assertIsNotNone(todo.id)
            mock_queue.assert_called_once_with(todo.id, operation="upsert")

    def test_update_todo_queues_vector_indexing(self):
        """update_todo: Todo更新時にベクトルインデックスがキューイングされる"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_update_123",
                "error": None,
            }

            validated_data = {"progress": 100}

            # Act
            updated_todo = TodoService.update_todo(
                self.todo1.id, self.user1, validated_data
            )

            # Assert
            mock_queue.assert_called_once_with(self.todo1.id, operation="upsert")

    def test_delete_todo_queues_vector_deletion(self):
        """delete_todo: Todo削除時にベクトル削除がキューイングされる"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_delete_123",
                "error": None,
            }

            todo_id = self.todo1.id

            # Act
            TodoService.delete_todo(todo_id, self.user1)

            # Assert
            mock_queue.assert_called_once_with(todo_id, operation="delete")
            # Todo自体も削除されているか確認
            self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_create_todo_continues_on_qstash_failure(self):
        """create_todo: QStashキューイング失敗でもTodo作成は成功する"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": False,
                "message_id": None,
                "error": "QStash error",
            }

            validated_data = {
                "todo_title": "新しいタスク",
                "priority": Todo.Priority.HIGH,
                "progress": 0,
            }

            # Act
            todo = TodoService.create_todo(self.user1, validated_data)

            # Assert - Todo作成は成功している
            self.assertIsNotNone(todo.id)
            self.assertEqual(todo.todo_title, "新しいタスク")
            # QStashは呼ばれた
            mock_queue.assert_called_once()

    # ============================================
    # MotherDuck Analytics のテスト
    # ============================================

    def test_create_todo_logs_analytics(self):
        """create_todo: Todo作成時に分析ログが記録される"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_create"
        ) as mock_analytics:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            validated_data = {
                "todo_title": "新しいタスク",
                "priority": Todo.Priority.HIGH,
                "progress": 0,
            }

            # Act
            todo = TodoService.create_todo(self.user1, validated_data)

            # Assert
            self.assertIsNotNone(todo.id)
            mock_analytics.assert_called_once_with(user=self.user1, todo=todo)

    def test_update_todo_logs_analytics_on_change(self):
        """update_todo: Todo更新時に分析ログが記録される（変更がある場合）"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_update"
        ) as mock_analytics:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            validated_data = {"todo_title": "更新されたタスク", "progress": 75}

            # Act
            updated_todo = TodoService.update_todo(
                self.todo1.id, self.user1, validated_data
            )

            # Assert
            self.assertEqual(updated_todo.todo_title, "更新されたタスク")
            mock_analytics.assert_called_once()

            # 呼び出し引数を確認
            call_kwargs = mock_analytics.call_args[1]
            self.assertEqual(call_kwargs["user"], self.user1)
            self.assertEqual(call_kwargs["todo"], updated_todo)
            self.assertIn("changed_fields", call_kwargs)

    def test_update_todo_logs_complete_event(self):
        """update_todo: 完了時に完了イベントがログされる"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_complete"
        ) as mock_complete, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_update"
        ) as mock_update:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            # 50% → 100% に更新
            validated_data = {"progress": 100}

            # Act
            updated_todo = TodoService.update_todo(
                self.todo1.id, self.user1, validated_data
            )

            # Assert
            self.assertEqual(updated_todo.progress, 100)
            # 完了イベントが記録される
            mock_complete.assert_called_once_with(user=self.user1, todo=updated_todo)
            # 通常の更新イベントは記録されない
            mock_update.assert_not_called()

    def test_update_todo_no_analytics_when_no_change(self):
        """update_todo: 変更がない場合は分析ログが記録されない"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_update"
        ) as mock_analytics:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            # 同じ値で更新（変更なし）
            validated_data = {
                "todo_title": "タスク1",  # 元の値と同じ
                "progress": 50,  # 元の値と同じ
            }

            # Act
            updated_todo = TodoService.update_todo(
                self.todo1.id, self.user1, validated_data
            )

            # Assert
            # 変更がないため、分析ログは記録されない
            mock_analytics.assert_not_called()

    def test_delete_todo_logs_analytics_with_reason(self):
        """delete_todo: Todo削除時に分析ログが記録される（理由付き）"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_delete"
        ) as mock_analytics:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            todo_id = self.todo1.id

            # Act
            TodoService.delete_todo(todo_id, self.user1)

            # Assert
            mock_analytics.assert_called_once()
            call_kwargs = mock_analytics.call_args[1]
            self.assertEqual(call_kwargs["user"], self.user1)
            self.assertEqual(
                call_kwargs["deletion_reason"], "cancelled"
            )  # progress < 100

    def test_delete_completed_todo_logs_completed_reason(self):
        """delete_todo: 完了済みTodo削除時は理由が'completed'"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_delete"
        ) as mock_analytics:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            # todo2はprogress=100
            todo_id = self.todo2.id

            # Act
            TodoService.delete_todo(todo_id, self.user1)

            # Assert
            mock_analytics.assert_called_once()
            call_kwargs = mock_analytics.call_args[1]
            self.assertEqual(
                call_kwargs["deletion_reason"], "completed"
            )  # progress == 100

    def test_analytics_continues_on_motherduck_failure(self):
        """create_todo: MotherDuck記録失敗でもTodo作成は成功する"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue, patch(
            "apps.todos.service.TodoAnalyticsService.log_todo_create"
        ) as mock_analytics:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }
            # MotherDuckへの記録が失敗
            mock_analytics.side_effect = Exception("MotherDuck connection error")

            validated_data = {
                "todo_title": "新しいタスク",
                "priority": Todo.Priority.HIGH,
                "progress": 0,
            }

            # Act - 例外は発生せず、Todo作成は成功するはず
            # （実装がtry-exceptで囲まれているか確認）
            todo = TodoService.create_todo(self.user1, validated_data)

            # Assert - Todo作成は成功している
            self.assertIsNotNone(todo.id)
            self.assertEqual(todo.todo_title, "新しいタスク")
