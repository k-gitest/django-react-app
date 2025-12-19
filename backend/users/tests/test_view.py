from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthenticationAPITest(TestCase):
    """
    dj-rest-auth APIエンドポイントのテスト
    """

    def setUp(self):
        """
        各テストの前に実行される初期化処理
        """
        self.client = APIClient()
        self.registration_url = reverse('rest_register')  # /api/v1/auth/registration/
        self.login_url = reverse('rest_login')            # /api/v1/auth/login/
        self.logout_url = reverse('rest_logout')          # /api/v1/auth/logout/
        self.user_url = reverse('rest_user_details')      # /api/v1/auth/user/

        # テスト用ユーザーデータ
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }

    def test_user_registration_success(self):
        """
        ユーザー登録が成功することを確認
        """
        data = {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

        # ユーザーがDBに作成されていることを確認
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_registration_with_duplicate_email(self):
        """
        重複したメールアドレスで登録しようとするとエラーが発生することを確認
        """
        # 最初のユーザー登録
        duplicate_email = 'duplicate@example.com'
        User.objects.create_user(
            email=duplicate_email,
            password='testpass123'
        )

        # 同じメールアドレスで再度登録を試みる
        data = {
            'email': duplicate_email,
            'password1': 'newpass456',
            'password2': 'newpass456',
        }

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_registration_password_mismatch(self):
        """
        パスワードが一致しない場合にエラーが発生することを確認
        """
        data = {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'different456',
        }

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """
        ログインが成功することを確認
        """
        # ユーザーを作成
        User.objects.create_user(**self.user_data)

        # ログイン
        response = self.client.post(self.login_url, self.user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)

        # Cookieが設定されていることを確認
        self.assertIn('access-token', response.cookies)
        self.assertIn('refresh-token', response.cookies)

    def test_user_login_with_wrong_password(self):
        """
        間違ったパスワードでログインしようとするとエラーが発生することを確認
        """
        # ユーザーを作成
        User.objects.create_user(**self.user_data)

        # 間違ったパスワードでログイン
        wrong_data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword',
        }

        response = self.client.post(self.login_url, wrong_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_with_nonexistent_email(self):
        """
        存在しないメールアドレスでログインしようとするとエラーが発生することを確認
        """
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123',
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_details_authenticated(self):
        """
        認証済みユーザーが自分の情報を取得できることを確認
        """
        # ユーザーを作成
        User.objects.create_user(**self.user_data)

        # ログインしてCookieを取得
        login_response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # ユーザー情報を取得（Cookieは自動的に送信される）
        response = self.client.get(self.user_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)

    def test_get_user_details_unauthenticated(self):
        """
        未認証ユーザーが情報を取得しようとすると401エラーが発生することを確認
        """
        response = self.client.get(self.user_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout_success(self):
        """
        ログアウトが成功することを確認
        """
        # ユーザーを作成
        User.objects.create_user(**self.user_data)

        # ログインしてCookieを取得
        login_response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Cookieが設定されていることを確認
        self.assertIn('access-token', login_response.cookies)

        # ログアウト（Cookieは自動的に送信される）
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_details(self):
        """
        ユーザー情報を更新できることを確認
        """
        # ユーザーを作成
        User.objects.create_user(**self.user_data)

        # ログインしてCookieを取得
        login_response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # 名前を更新
        update_data = {
            'first_name': 'John',
            'last_name': 'Doe',
        }

        response = self.client.patch(self.user_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')

        # DBも更新されていることを確認
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')


class TokenRefreshAPITest(TestCase):
    """
    トークンリフレッシュAPIのテスト
    """

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = reverse('token_refresh')  # /api/v1/auth/token/refresh/
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }

    def test_token_refresh_with_valid_cookie(self):
        """
        有効なrefresh-token Cookieでトークンをリフレッシュできることを確認
        """
        # ユーザーを作成してログイン
        User.objects.create_user(**self.user_data)
        login_url = reverse('rest_login')
        login_response = self.client.post(login_url, self.user_data, format='json')

        # refresh-token Cookieを取得
        refresh_cookie = login_response.cookies.get('refresh-token')
        self.assertIsNotNone(refresh_cookie)

        # Cookieを設定してリフレッシュ
        self.client.cookies['refresh-token'] = refresh_cookie.value
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_without_cookie(self):
        """
        refresh-token Cookieなしでリフレッシュしようとすると401エラーが発生することを確認
        """
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)