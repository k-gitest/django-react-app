"""
Tests for TodoQuery（pytest）
"""
import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory

from apps.todos.models import Todo
from apps.graphql_api.context import get_context
from apps.graphql_api.schema import schema

User = get_user_model()


@pytest.mark.django_db
class TestTodoQuery:
    """TodoQuery のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.todo1 = Todo.objects.create(
            user=self.user,
            todo_title="Todo 1",
            priority="HIGH",
            progress=50
        )
        self.todo2 = Todo.objects.create(
            user=self.user,
            todo_title="Todo 2",
            priority="MEDIUM",
            progress=30
        )

    @pytest.fixture
    def execute_query(self):
        """GraphQL Query を実行するフィクスチャ"""
        def _execute(query: str, user=None, variables: dict = None):
            factory = RequestFactory()
            request = factory.get("/graphql")
            request.user = user if user else self.user

            response = HttpResponse()
            context = get_context(request, response)

            return schema.execute_sync(
                query,
                variable_values=variables,
                context_value=context
            )
        return _execute

    def test_todos_list(self, execute_query):
        """Todo一覧取得"""
        query = """
            query {
                todos {
                    todoTitle
                    priority
                    progress
                }
            }
        """

        result = execute_query(query)

        assert result.errors is None

        todos = result.data["todos"]
        todo_titles = [t["todoTitle"] for t in todos]
        assert "Todo 1" in todo_titles
        assert "Todo 2" in todo_titles
        assert len(todos) == 2

    def test_priority_stats(self, execute_query):
        """優先度統計取得"""
        query = """
            query {
                priorityStats {
                    priority
                    count
                }
            }
        """

        result = execute_query(query)

        assert result.errors is None

        stats = result.data["priorityStats"]
        high_stat = next((s for s in stats if s["priority"] == "HIGH"), None)

        assert high_stat is not None
        assert high_stat["count"] == 1