"""
Tests for UserMutation
"""
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from apps.graphql_api.schema import schema
from apps.graphql_api.context import get_context

User = get_user_model()


class UserMutationTestCase(TestCase):
    """UserMutation のテスト"""
    
    def _execute_mutation(self, mutation: str, variables: dict = None, authenticated: bool = False, user=None):
        """GraphQL Mutationを実行するヘルパー"""
        from django.test import RequestFactory
        from django.http import HttpResponse
        
        factory = RequestFactory()
        request = factory.post('/graphql')
        
        if authenticated and user:
            request.user = user
        elif not authenticated:
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
    @patch('apps.users.user_service.UserQStashService.send_welcome_email_async')
    def test_register_success(self, mock_send_email):
        """ユーザー登録成功"""
        mutation = """
            mutation Register($input: RegisterInput!) {
                register(input: $input) {
                    ... on AuthPayload {
                        user {
                            email
                            fullName
                        }
                        message
                    }
                }
            }
        """
        
        variables = {
            "input": {
                "email": "newuser@example.com",
                "password": "testpass123",
                "passwordConfirm": "testpass123",
                "firstName": "太郎",
                "lastName": "山田"
            }
        }
        
        result = self._execute_mutation(mutation, variables)
        
        self.assertIsNone(result.errors)
        
        data = result.data['register']
        self.assertEqual(data['user']['email'], 'newuser@example.com')
        self.assertEqual(data['user']['fullName'], '山田 太郎')
        
        # ユーザーが作成されているか確認
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_register_validation_error(self):
        """バリデーションエラー（パスワード不一致）"""
        mutation = """
            mutation Register($input: RegisterInput!) {
                register(input: $input) {
                    ... on ValidationError {
                        message
                        field
                    }
                }
            }
        """
        
        variables = {
            "input": {
                "email": "test@example.com",
                "password": "password123",
                "passwordConfirm": "different",
                "firstName": "",
                "lastName": ""
            }
        }
        
        result = self._execute_mutation(mutation, variables)
        
        self.assertIsNone(result.errors)
        
        data = result.data['register']
        self.assertEqual(data['field'], 'password_confirm')
        self.assertIn('一致しません', data['message'])
    
    @override_settings(TESTING=True)
    def test_login_success(self):
        """ログイン成功"""
        # 事前にユーザーを作成
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        mutation = """
            mutation Login($input: LoginInput!) {
                login(input: $input) {
                    ... on AuthPayload {
                        user {
                            email
                        }
                        message
                    }
                }
            }
        """
        
        variables = {
            "input": {
                "email": "test@example.com",
                "password": "testpass123"
            }
        }
        
        result = self._execute_mutation(mutation, variables)
        
        self.assertIsNone(result.errors)
        
        data = result.data['login']
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertIn('ログインしました', data['message'])
    
    def test_login_invalid_credentials(self):
        """ログイン失敗（無効な認証情報）"""
        User.objects.create_user(
            email='test@example.com',
            password='correctpass'
        )
        
        mutation = """
            mutation Login($input: LoginInput!) {
                login(input: $input) {
                    ... on ValidationError {
                        message
                    }
                }
            }
        """
        
        variables = {
            "input": {
                "email": "test@example.com",
                "password": "wrongpass"
            }
        }
        
        result = self._execute_mutation(mutation, variables)
        
        self.assertIsNone(result.errors)
        
        data = result.data['login']
        self.assertIn('正しくありません', data['message'])