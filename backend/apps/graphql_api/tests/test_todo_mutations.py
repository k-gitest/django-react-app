"""
Tests for TodoMutation
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from graphql import GraphQLError

from apps.todos.models import Todo
from apps.graphql_api.schema import schema
from apps.graphql_api.context import get_context

User = get_user_model()


class TodoMutationTestCase(TestCase):
    """TodoMutation のテスト"""
    
    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
    
    def _execute_mutation(self, mutation: str, variables: dict = None, authenticated: bool = True):
        """
        GraphQL Mutationを実行するヘルパー
        
        Args:
            mutation: GraphQL mutation文字列
            variables: 変数辞書
            authenticated: 認証済みユーザーでテストするか
        
        Returns:
            実行結果
        """
        from django.test import RequestFactory
        from django.http import HttpResponse
        
        factory = RequestFactory()
        request = factory.post('/graphql')
        
        if authenticated:
            request.user = self.user
        else:
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
        
        response = HttpResponse()
        context = get_context(request, response)
        
        result = schema.execute_sync(
            mutation,
            variable_values=variables,
            context_value=context
        )
        
        return result
    
    @override_settings(TESTING=True)
    def test_create_todo_success(self):
        """Todo作成成功"""
        mutation = """
            mutation CreateTodo($input: TodoCreateInput!) {
                createTodo(input: $input) {
                    ... on CreateTodoPayload {
                        todoEdge {
                            node {
                                todoTitle
                                priority
                                progress
                            }
                        }
                    }
                    ... on ValidationError {
                        message
                        field
                    }
                }
            }
        """
        
        variables = {
            "input": {
                "todoTitle": "Test Todo",
                "priority": "HIGH",
                "progress": 0
            }
        }
        
        result = self._execute_mutation(mutation, variables)
        
        # エラーがないことを確認
        self.assertIsNone(result.errors)
        
        # データの確認
        data = result.data['createTodo']
        self.assertIn('todoEdge', data)
        self.assertEqual(data['todoEdge']['node']['todoTitle'], 'Test Todo')
        self.assertEqual(data['todoEdge']['node']['priority'], 'HIGH')
        
        # DBに保存されているか確認
        self.assertTrue(Todo.objects.filter(todo_title='Test Todo').exists())
    
    def test_create_todo_validation_error(self):
        """バリデーションエラー（空のタイトル）"""
        mutation = """
            mutation CreateTodo($input: TodoCreateInput!) {
                createTodo(input: $input) {
                    ... on ValidationError {
                        message
                        field
                        code
                    }
                }
            }
        """
        
        variables = {
            "input": {
                "todoTitle": "",  # 空文字
                "priority": "MEDIUM",
                "progress": 0
            }
        }
        
        result = self._execute_mutation(mutation, variables)
        
        self.assertIsNone(result.errors)
        
        data = result.data['createTodo']
        self.assertEqual(data['field'], 'todo_title')
        self.assertIn('空にできません', data['message'])
    
    def test_create_todo_unauthenticated(self):
        """未認証でのアクセス"""
        mutation = """
            mutation CreateTodo($input: TodoCreateInput!) {
                createTodo(input: $input) {
                    ... on CreateTodoPayload {
                        todoEdge {
                            node {
                                todoTitle
                            }
                        }
                    }
                }
            }
        """
        
        variables = {
            "input": {
                "todoTitle": "Test",
                "priority": "MEDIUM",
                "progress": 0
            }
        }
        
        result = self._execute_mutation(mutation, variables, authenticated=False)
        
        # 認証エラーが返される
        self.assertIsNotNone(result.errors)
        self.assertIn('認証が必要です', str(result.errors[0]))
    
    @override_settings(TESTING=True)
    def test_update_todo_success(self):
        """Todo更新成功"""
        # 事前にTodoを作成
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Original Title",
            progress=0
        )
        
        mutation = """
            mutation UpdateTodo($id: ID!, $input: TodoUpdateInput!) {
                updateTodo(id: $id, input: $input) {
                    ... on UpdateTodoPayload {
                        todo {
                            todoTitle
                            progress
                        }
                    }
                }
            }
        """
        
        # GlobalIDに変換
        from strawberry import relay
        global_id = relay.to_base64("TodoType", todo.id)
        
        variables = {
            "id": global_id,
            "input": {
                "todoTitle": "Updated Title",
                "progress": 50
            }
        }
        
        result = self._execute_mutation(mutation, variables)
        
        self.assertIsNone(result.errors)
        
        data = result.data['updateTodo']
        self.assertEqual(data['todo']['todoTitle'], 'Updated Title')
        self.assertEqual(data['todo']['progress'], 50)
    
    @override_settings(TESTING=True)
    def test_delete_todo_success(self):
        """Todo削除成功"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Delete Me"
        )
        
        mutation = """
            mutation DeleteTodo($id: ID!) {
                deleteTodo(id: $id) {
                    ... on DeleteTodoPayload {
                        deletedTodoId
                        message
                    }
                }
            }
        """
        
        from strawberry import relay
        global_id = relay.to_base64("TodoType", todo.id)
        
        variables = {"id": global_id}
        
        result = self._execute_mutation(mutation, variables)
        
        self.assertIsNone(result.errors)
        
        data = result.data['deleteTodo']
        self.assertIn('削除しました', data['message'])
        
        # DBから削除されているか確認
        self.assertFalse(Todo.objects.filter(id=todo.id).exists())