"""
Tests for TodoQuery
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.todos.models import Todo
from apps.graphql_api.schema import schema
from apps.graphql_api.context import get_context

User = get_user_model()


class TodoQueryTestCase(TestCase):
    """TodoQuery のテスト"""
    
    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        # テスト用Todoを作成
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
    
    def _execute_query(self, query: str, variables: dict = None):
        """GraphQL Queryを実行するヘルパー"""
        from django.test import RequestFactory
        from django.http import HttpResponse
        
        factory = RequestFactory()
        request = factory.get('/graphql')
        request.user = self.user
        
        response = HttpResponse()
        context = get_context(request, response)
        
        result = schema.execute_sync(
            query,
            variable_values=variables,
            context_value=context
        )
        
        return result
    
    def test_todos_list(self):
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
        
        result = self._execute_query(query)
        
        self.assertIsNone(result.errors)
        
        todos = result.data['todos']
        todo_titles = [t['todoTitle'] for t in todos]
        self.assertIn('Todo 1', todo_titles)
        self.assertIn('Todo 2', todo_titles)
        self.assertEqual(len(todos), 2)
    
    def test_priority_stats(self):
        """優先度統計取得"""
        query = """
            query {
                priorityStats {
                    priority
                    count
                }
            }
        """
        
        result = self._execute_query(query)
        
        self.assertIsNone(result.errors)
        
        stats = result.data['priorityStats']
        high_stat = next((s for s in stats if s['priority'] == 'HIGH'), None)
        
        self.assertIsNotNone(high_stat)
        self.assertEqual(high_stat['count'], 1)