from unittest.mock import MagicMock, PropertyMock, patch

from apps.todos.models import Todo
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class TodoViewSetTestCase(TestCase):
    """TodoViewSetのAPIテスト"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        self.client = APIClient()

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
            todo_title="User1のタスク1",
            priority=Todo.Priority.HIGH,
            progress=50,
        )
        self.todo2 = Todo.objects.create(
            user=self.user1,
            todo_title="User1のタスク2",
            priority=Todo.Priority.MEDIUM,
            progress=100,
        )
        self.todo3 = Todo.objects.create(
            user=self.user2,
            todo_title="User2のタスク",
            priority=Todo.Priority.LOW,
            progress=0,
        )

    def test_list_todos_unauthenticated(self):
        """一覧取得: 未認証ユーザーは401"""
        response = self.client.get("/api/v1/todos/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_todos_authenticated(self):
        """一覧取得: 認証済みユーザーは自分のタスクのみ取得"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/todos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # 自分のタスクのみ含まれる
        titles = [todo["todo_title"] for todo in response.data]
        self.assertIn("User1のタスク1", titles)
        self.assertIn("User1のタスク2", titles)
        self.assertNotIn("User2のタスク", titles)

    def test_retrieve_todo_success(self):
        """詳細取得: 自分のタスクは取得可能"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/v1/todos/{self.todo1.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["todo_title"], "User1のタスク1")
        self.assertEqual(response.data["priority"], "HIGH")
        self.assertEqual(response.data["progress"], 50)

    def test_retrieve_todo_unauthorized(self):
        """詳細取得: 他人のタスクは取得不可（404）"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f"/api/v1/todos/{self.todo3.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_todo_success(self):
        """作成: 正常なデータでタスクを作成"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            self.client.force_authenticate(user=self.user1)
            data = {"todo_title": "新しいタスク", "priority": "HIGH", "progress": 0}

            response = self.client.post("/api/v1/todos/", data)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["todo_title"], "新しいタスク")
            self.assertEqual(response.data["priority"], "HIGH")

            # DBに保存されているか確認
            self.assertTrue(
                Todo.objects.filter(user=self.user1, todo_title="新しいタスク").exists()
            )

    def test_create_todo_with_default_values(self):
        """作成: 最小限のデータで作成（デフォルト値使用）"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            self.client.force_authenticate(user=self.user1)
            data = {"todo_title": "シンプルなタスク"}

            response = self.client.post("/api/v1/todos/", data)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data["priority"], "MEDIUM")  # デフォルト
            self.assertEqual(response.data["progress"], 0)  # デフォルト

    def test_create_todo_invalid_priority(self):
        """作成: 無効な優先度で400エラー"""
        self.client.force_authenticate(user=self.user1)
        data = {"todo_title": "テストタスク", "priority": "INVALID"}

        response = self.client.post("/api/v1/todos/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_todo_missing_title(self):
        """作成: タイトルなしで400エラー"""
        self.client.force_authenticate(user=self.user1)
        data = {"priority": "HIGH"}

        response = self.client.post("/api/v1/todos/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("todo_title", response.data)

    def test_update_todo_success(self):
        """更新: 自分のタスクを更新"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            self.client.force_authenticate(user=self.user1)
            data = {"todo_title": "更新されたタスク", "progress": 75}

            response = self.client.patch(f"/api/v1/todos/{self.todo1.id}/", data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["todo_title"], "更新されたタスク")
            self.assertEqual(response.data["progress"], 75)

            # DBも更新されているか確認
            self.todo1.refresh_from_db()
            self.assertEqual(self.todo1.todo_title, "更新されたタスク")
            self.assertEqual(self.todo1.progress, 75)

    def test_update_todo_partial(self):
        """更新: 部分更新が可能"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            self.client.force_authenticate(user=self.user1)
            data = {"progress": 100}

            response = self.client.patch(f"/api/v1/todos/{self.todo1.id}/", data)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["progress"], 100)
            self.assertEqual(response.data["todo_title"], "User1のタスク1")  # 変更なし

    def test_update_todo_unauthorized(self):
        """更新: 他人のタスクは更新不可（404）"""
        self.client.force_authenticate(user=self.user1)
        data = {"progress": 100}

        response = self.client.patch(f"/api/v1/todos/{self.todo3.id}/", data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_todo_success(self):
        """削除: 自分のタスクを削除"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_123",
                "error": None,
            }

            self.client.force_authenticate(user=self.user1)
            todo_id = self.todo1.id

            response = self.client.delete(f"/api/v1/todos/{todo_id}/")

            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

            # DBから削除されているか確認
            self.assertFalse(Todo.objects.filter(id=todo_id).exists())

    def test_delete_todo_unauthorized(self):
        """削除: 他人のタスクは削除不可（404）"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.delete(f"/api/v1/todos/{self.todo3.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # DBに残っているか確認
        self.assertTrue(Todo.objects.filter(id=self.todo3.id).exists())

    def test_stats_action_success(self):
        """カスタムアクション: stats - 優先度別統計"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.get("/api/v1/todos/stats/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        # データ構造の確認
        stats_dict = {item["priority"]: item["count"] for item in response.data}
        self.assertEqual(stats_dict.get("HIGH", 0), 1)
        self.assertEqual(stats_dict.get("MEDIUM", 0), 1)

    def test_stats_action_unauthenticated(self):
        """カスタムアクション: stats - 未認証は401"""
        response = self.client.get("/api/v1/todos/stats/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_progress_stats_action_success(self):
        """カスタムアクション: progress-stats - 進捗率別統計"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.get("/api/v1/todos/progress-stats/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

        # 必要なキーが含まれているか確認
        expected_keys = [
            "range_0_20",
            "range_21_40",
            "range_41_60",
            "range_61_80",
            "range_81_100",
        ]
        for key in expected_keys:
            self.assertIn(key, response.data)

        # 実際の値を確認
        self.assertEqual(response.data["range_41_60"], 1)  # progress=50
        self.assertEqual(response.data["range_81_100"], 1)  # progress=100

    def test_progress_stats_action_unauthenticated(self):
        """カスタムアクション: progress-stats - 未認証は401"""
        response = self.client.get("/api/v1/todos/progress-stats/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_isolation(self):
        """ユーザー分離: 各ユーザーは自分のデータのみアクセス可能"""
        # User1でログイン
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get("/api/v1/todos/")
        user1_count = len(response1.data)

        # User2でログイン
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get("/api/v1/todos/")
        user2_count = len(response2.data)

        # それぞれのタスク数が正しい
        self.assertEqual(user1_count, 2)
        self.assertEqual(user2_count, 1)

    # ============================================
    # 🆕 ベクトル検索エンドポイントのテスト
    # ============================================

    def test_search_action_success(self):
        """カスタムアクション: search - セマンティック検索成功"""
        from unittest.mock import MagicMock, patch

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

            self.client.force_authenticate(user=self.user1)
            response = self.client.get("/api/v1/todos/search/", {"q": "明日の会議"})

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["query"], "明日の会議")
            self.assertEqual(response.data["count"], 1)
            self.assertEqual(len(response.data["results"]), 1)
            self.assertEqual(response.data["results"][0]["score"], 0.85)

    def test_search_action_missing_query(self):
        """カスタムアクション: search - クエリなしで400エラー"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/v1/todos/search/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_search_action_with_parameters(self):
        """カスタムアクション: search - パラメータ付き検索"""
        from unittest.mock import MagicMock, patch

        with patch(
            "apps.todos.vector_service.VectorService"
        ) as mock_vector_service_class:
            mock_instance = MagicMock()
            mock_instance.search_similar.return_value = []
            mock_vector_service_class.return_value = mock_instance

            self.client.force_authenticate(user=self.user1)
            response = self.client.get(
                "/api/v1/todos/search/", {"q": "テスト", "top_k": 10, "min_score": 0.6}
            )

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["count"], 0)

            # VectorService が正しいパラメータで呼ばれたか確認
            mock_instance.search_similar.assert_called_once_with(
                "テスト", self.user1.id, 10, 0.6
            )

    def test_search_action_invalid_top_k(self):
        """カスタムアクション: search - 無効なtop_kで400エラー"""
        self.client.force_authenticate(user=self.user1)

        # top_k が範囲外
        response = self.client.get(
            "/api/v1/todos/search/", {"q": "テスト", "top_k": 200}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_action_invalid_min_score(self):
        """カスタムアクション: search - 無効なmin_scoreで400エラー"""
        self.client.force_authenticate(user=self.user1)

        # min_score が範囲外
        response = self.client.get(
            "/api/v1/todos/search/", {"q": "テスト", "min_score": 1.5}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_action_unauthenticated(self):
        """カスタムアクション: search - 未認証は401"""
        response = self.client.get("/api/v1/todos/search/", {"q": "テスト"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bulk_index_action_success(self):
        """カスタムアクション: bulk-index - 一括インデックス成功"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_bulk_vector_indexing"
        ) as mock_queue:
            mock_queue.return_value = {
                "success": True,
                "message_id": "msg_bulk_123",
                "error": None,
            }

            self.client.force_authenticate(user=self.user1)
            response = self.client.post("/api/v1/todos/bulk-index/")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "queued")
            self.assertIn("message", response.data)

    def test_bulk_index_action_error(self):
        """カスタムアクション: bulk-index - エラー時は500"""
        from unittest.mock import patch

        with patch(
            "apps.todos.service.TodoQStashService.queue_bulk_vector_indexing"
        ) as mock_queue:
            mock_queue.side_effect = Exception("Queue error")

            self.client.force_authenticate(user=self.user1)
            response = self.client.post("/api/v1/todos/bulk-index/")

            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            self.assertIn("error", response.data)

    def test_bulk_index_action_unauthenticated(self):
        """カスタムアクション: bulk-index - 未認証は401"""
        response = self.client.post("/api/v1/todos/bulk-index/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================
# 🆕 Webhook エンドポイントのテスト
# ============================================


class VectorIndexingWebhookTestCase(TestCase):
    """Vector indexing webhook のテスト"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="テストタスク",
            priority=Todo.Priority.HIGH,
            progress=50,
        )

    @patch("apps.common.permissions.verify_qstash_signature")
    @patch("apps.todos.views.VectorService")
    def test_vector_indexing_webhook_upsert_success(
        self, mock_vector_service_class, mock_verify
    ):
        """Webhook: upsert操作が成功する"""
        # Arrange
        mock_verify.return_value = True  # ← 署名検証を通過
        mock_instance = MagicMock()
        mock_vector_service_class.return_value = mock_instance

        payload = {"todo_id": self.todo.id, "operation": "upsert"}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["operation"], "upsert")
        mock_instance.add_todo.assert_called_once()

    @patch("apps.common.permissions.verify_qstash_signature")
    @patch("apps.todos.views.VectorService")
    def test_vector_indexing_webhook_delete_success(
        self, mock_vector_service_class, mock_verify
    ):
        """Webhook: delete操作が成功する"""
        # Arrange
        mock_verify.return_value = True  # ← 署名検証を通過
        mock_instance = MagicMock()
        mock_vector_service_class.return_value = mock_instance

        payload = {"todo_id": self.todo.id, "operation": "delete"}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["operation"], "delete")
        mock_instance.delete_todo.assert_called_once_with(self.todo.id)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_vector_indexing_webhook_missing_todo_id(self, mock_verify):
        """Webhook: todo_idなしで400エラー"""
        # Arrange
        mock_verify.return_value = True  # ← 署名検証を通過

        payload = {"operation": "upsert"}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_vector_indexing_webhook_invalid_signature(self, mock_verify):
        """Webhook: 無効な署名で401エラー（認証失敗）"""
        # Arrange
        mock_verify.return_value = False  # ← 署名検証を失敗させる

        payload = {"todo_id": self.todo.id}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BulkVectorIndexingWebhookTestCase(TestCase):
    """Bulk vector indexing webhook のテスト"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        Todo.objects.create(
            user=self.user, todo_title="タスク1", priority=Todo.Priority.HIGH
        )
        Todo.objects.create(
            user=self.user, todo_title="タスク2", priority=Todo.Priority.MEDIUM
        )

    @patch("apps.common.permissions.verify_qstash_signature")
    @patch("apps.todos.views.VectorService")
    def test_bulk_vector_indexing_webhook_success(
        self, mock_vector_service_class, mock_verify
    ):
        """Webhook: 一括インデックスが成功する"""
        # Arrange
        mock_verify.return_value = True  # ← 署名検証を通過
        mock_instance = MagicMock()
        mock_vector_service_class.return_value = mock_instance

        payload = {"user_id": self.user.id}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/bulk-vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        mock_instance.add_todos_batch.assert_called_once()

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_bulk_vector_indexing_webhook_no_todos(self, mock_verify):
        """Webhook: Todoがない場合"""
        # Arrange
        mock_verify.return_value = True  # ← 署名検証を通過

        new_user = User.objects.create_user(
            email="newuser@example.com", password="testpass123"
        )

        payload = {"user_id": new_user.id}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/bulk-vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_bulk_vector_indexing_webhook_missing_user_id(self, mock_verify):
        """Webhook: user_idなしで400エラー"""
        # Arrange
        mock_verify.return_value = True  # ← 署名検証を通過

        payload = {}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/bulk-vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_bulk_vector_indexing_webhook_invalid_signature(self, mock_verify):
        """Webhook: 無効な署名で401エラー（認証失敗）"""
        # Arrange
        mock_verify.return_value = False  # ← 署名検証を失敗させる

        payload = {"user_id": self.user.id}

        # Act
        response = self.client.post(
            "/api/v1/webhooks/bulk-vector-indexing", data=payload, format="json"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
