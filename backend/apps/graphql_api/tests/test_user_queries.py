"""
Tests for UserQuery
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from apps.graphql_api.schema import schema
from apps.graphql_api.context import get_context

User = get_user_model()

class UserQueryTestCase(TestCase):
    """UserQuery のテスト"""

    def setUp(self):
        """テストデータの準備"""
        # テストユーザー1 (一般ユーザー)
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        # テストユーザー2 (別の一般ユーザー)
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
        )
        # スタッフユーザー
        self.staff_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )

    def _execute_query(self, query: str, user=None, variables: dict = None):
        """GraphQL Queryを実行するヘルパー"""
        factory = RequestFactory()
        request = factory.get('/graphql')
        
        # 指定されたユーザーで認証状態をシミュレート
        request.user = user if user else self.user
        
        response = HttpResponse()
        context = get_context(request, response)
        
        result = schema.execute_sync(
            query,
            variable_values=variables,
            context_value=context
        )
        return result

    def test_me_query_success(self):
        """ログイン中の自分の情報を取得できるか"""
        query = """
            query {
                me {
                    email
                    isStaff
                }
            }
        """
        result = self._execute_query(query, user=self.user)
        
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['me']['email'], self.user.email)
        self.assertFalse(result.data['me']['isStaff'])

    def test_user_query_own_profile(self):
        """自分のIDを指定して情報を取得できるか"""
        query = """
            query($id: Int!) {
                user(id: $id) {
                    email
                }
            }
        """
        variables = {"id": self.user.id}
        result = self._execute_query(query, user=self.user, variables=variables)
        
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['user']['email'], self.user.email)

    def test_user_query_other_profile_denied(self):
        """一般ユーザーが他人の情報を取得しようとすると None が返るか"""
        query = """
            query($id: Int!) {
                user(id: $id) {
                    email
                }
            }
        """
        # self.user (ID=1) が self.other_user (ID=2) を見ようとする
        variables = {"id": self.other_user.id}
        result = self._execute_query(query, user=self.user, variables=variables)
        
        # エラーにはならず、ロジック通り None (null) が返ることを確認
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['user'])

    def test_user_query_by_staff(self):
        """スタッフ権限があれば他人の情報も取得できるか"""
        query = """
            query($id: Int!) {
                user(id: $id) {
                    email
                }
            }
        """
        # 管理者が一般ユーザーの情報を取得
        variables = {"id": self.user.id}
        result = self._execute_query(query, user=self.staff_user, variables=variables)
        
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['user']['email'], self.user.email)