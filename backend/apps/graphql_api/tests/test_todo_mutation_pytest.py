"""
Tests for TodoMutation（pytest）
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from apps.todos.models import Todo
from apps.graphql_api.context import get_context
from apps.graphql_api.schema import schema

User = get_user_model()


@pytest.mark.django_db
class TestTodoMutation:
    """TodoMutation のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

    @pytest.fixture
    def execute_mutation(self):
        """GraphQL Mutation を実行するフィクスチャ"""
        def _execute(mutation: str, variables: dict = None, authenticated: bool = True):
            factory = RequestFactory()
            request = factory.post("/graphql")
            request.user = self.user if authenticated else AnonymousUser()

            response = HttpResponse()
            context = get_context(request, response)

            return schema.execute_sync(
                mutation,
                variable_values=variables,
                context_value=context
            )
        return _execute

    @override_settings(TESTING=True)
    def test_create_todo_success(self, execute_mutation):
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

        result = execute_mutation(mutation, variables)

        assert result.errors is None

        data = result.data["createTodo"]
        assert "todoEdge" in data
        assert data["todoEdge"]["node"]["todoTitle"] == "Test Todo"
        assert data["todoEdge"]["node"]["priority"] == "HIGH"
        assert Todo.objects.filter(todo_title="Test Todo").exists()

    def test_create_todo_validation_error(self, execute_mutation):
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

        result = execute_mutation(mutation, variables)

        assert result.errors is None

        data = result.data["createTodo"]
        assert data["field"] == "todo_title"
        assert "空にできません" in data["message"]

    def test_create_todo_unauthenticated(self, execute_mutation):
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

        result = execute_mutation(mutation, variables, authenticated=False)

        assert result.errors is not None
        assert "認証が必要です" in str(result.errors[0])

    @override_settings(TESTING=True)
    def test_update_todo_success(self, execute_mutation):
        """Todo更新成功"""
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

        from strawberry import relay
        global_id = relay.to_base64("TodoType", todo.id)

        variables = {
            "id": global_id,
            "input": {
                "todoTitle": "Updated Title",
                "progress": 50
            }
        }

        result = execute_mutation(mutation, variables)

        assert result.errors is None

        data = result.data["updateTodo"]
        assert data["todo"]["todoTitle"] == "Updated Title"
        assert data["todo"]["progress"] == 50

    @override_settings(TESTING=True)
    def test_delete_todo_success(self, execute_mutation):
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

        result = execute_mutation(mutation, {"id": global_id})

        assert result.errors is None

        data = result.data["deleteTodo"]
        assert "削除しました" in data["message"]
        assert not Todo.objects.filter(id=todo.id).exists()