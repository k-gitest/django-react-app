"""
Tests for UserQuery（pytest）
"""
import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory

from apps.graphql_api.context import get_context
from apps.graphql_api.schema import schema

User = get_user_model()


@pytest.mark.django_db
class TestUserQuery:
    """UserQuery のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123"
        )
        self.staff_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
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

    def test_me_query_success(self, execute_query):
        """ログイン中の自分の情報を取得できるか"""
        query = """
            query {
                me {
                    email
                    isStaff
                }
            }
        """

        result = execute_query(query, user=self.user)

        assert result.errors is None
        assert result.data["me"]["email"] == self.user.email
        assert result.data["me"]["isStaff"] is False

    def test_user_query_own_profile(self, execute_query):
        """自分のIDを指定して情報を取得できるか"""
        query = """
            query($id: Int!) {
                user(id: $id) {
                    email
                }
            }
        """

        result = execute_query(query, user=self.user, variables={"id": self.user.id})

        assert result.errors is None
        assert result.data["user"]["email"] == self.user.email

    def test_user_query_other_profile_denied(self, execute_query):
        """一般ユーザーが他人の情報を取得しようとすると None が返るか"""
        query = """
            query($id: Int!) {
                user(id: $id) {
                    email
                }
            }
        """

        result = execute_query(query, user=self.user, variables={"id": self.other_user.id})

        assert result.errors is None
        assert result.data["user"] is None

    def test_user_query_by_staff(self, execute_query):
        """スタッフ権限があれば他人の情報も取得できるか"""
        query = """
            query($id: Int!) {
                user(id: $id) {
                    email
                }
            }
        """

        result = execute_query(query, user=self.staff_user, variables={"id": self.user.id})

        assert result.errors is None
        assert result.data["user"]["email"] == self.user.email