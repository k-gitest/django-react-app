from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

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
        self.registration_url = reverse('rest_register')
        self.login_url = reverse('rest_login')
        self.logout_url = reverse('rest_logout')
        self.user_url = reverse('rest_user_details')

        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }

    @patch('users.views.AnalyticsService.log_auth_event')  # ← 追加
    def test_user_registration_success(self, mock_log_auth):
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
        
        # 分析ログが記録されたことを確認
        mock_log_auth.assert_called_once()
        call_kwargs = mock_log_auth.call_args[1]
        self.assertEqual(call_kwargs['event_type'], 'register')
        self.assertTrue(call_kwargs['success'])

    def test_user_registration_with_duplicate_email(self):
        """
        重複したメールアドレスで登録しようとするとエラーが発生することを確認
        """
        duplicate_email = 'duplicate@example.com'
        User.objects.create_user(
            email=duplicate_email,
            password='testpass123'
        )

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

    @patch('users.views.MotherDuckClient')
    def test_user_login_success(self, mock_motherduck_class):
        """
        ログインが成功することを確認
        """
        # Arrange
        mock_client = MagicMock()
        mock_motherduck_class.return_value = mock_client
        
        User.objects.create_user(**self.user_data)

        # Act
        response = self.client.post(self.login_url, self.user_data, format='json')

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertIn('access-token', response.cookies)
        self.assertIn('refresh-token', response.cookies)
        
        # 分析ログは副作用なのでテストしない
        # （別のテストケースで詳細にテスト済み）

    def test_user_login_with_wrong_password(self):
        """
        間違ったパスワードでログインしようとするとエラーが発生することを確認
        """
        User.objects.create_user(**self.user_data)

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
        User.objects.create_user(**self.user_data)

        login_response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

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

    @patch('users.views.MotherDuckClient')
    def test_user_logout_success(self, mock_motherduck_class):
        """
        ログアウトが成功することを確認
        """
        # Arrange
        mock_client = MagicMock()
        mock_motherduck_class.return_value = mock_client
        
        User.objects.create_user(**self.user_data)

        login_response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Act
        response = self.client.post(self.logout_url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_details(self):
        """
        ユーザー情報を更新できることを確認
        """
        User.objects.create_user(**self.user_data)

        login_response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        update_data = {
            'first_name': 'John',
            'last_name': 'Doe',
        }

        response = self.client.patch(self.user_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')
        self.assertEqual(response.data['last_name'], 'Doe')

        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')


class TokenRefreshAPITest(TestCase):
    """
    トークンリフレッシュAPIのテスト
    """

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = reverse('token_refresh')
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }

    def test_token_refresh_with_valid_cookie(self):
        """
        有効なrefresh-token Cookieでトークンをリフレッシュできることを確認
        """
        User.objects.create_user(**self.user_data)
        login_url = reverse('rest_login')
        login_response = self.client.post(login_url, self.user_data, format='json')

        refresh_cookie = login_response.cookies.get('refresh-token')
        self.assertIsNotNone(refresh_cookie)

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


# ============================================
# 🆕 Webhook エンドポイントのテスト
# ============================================

class AnalyticsEventWebhookTestCase(TestCase):
    """Analytics event webhook のテスト"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/webhooks/analytics-event'
    
    @patch('common.permissions.verify_qstash_signature')
    @patch('users.views.MotherDuckClient')
    def test_analytics_event_webhook_auth_event_success(self, mock_motherduck_class, mock_verify):
        """Webhook: auth_event が正しく記録される"""
        # Arrange
        mock_verify.return_value = True
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client
        
        payload = {
            'event_type': 'auth_event',
            'event_data': {
                'user_id': 1,
                'email': 'test@example.com',
                'event_type': 'login',
                'ip_address': '192.168.1.1',
                'success': True
            }
        }
        
        # Act
        response = self.client.post(self.url, data=payload, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_type'], 'auth_event')
        mock_client.insert_auth_event.assert_called_once_with(payload['event_data'])
    
    @patch('common.permissions.verify_qstash_signature')
    def test_analytics_event_webhook_missing_event_type(self, mock_verify):
        """Webhook: event_type なしで400エラー"""
        # Arrange
        mock_verify.return_value = True
        payload = {'event_data': {}}
        
        # Act
        response = self.client.post(self.url, data=payload, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('common.permissions.verify_qstash_signature')
    def test_analytics_event_webhook_unknown_event_type(self, mock_verify):
        """Webhook: 未知のevent_typeで400エラー"""
        # Arrange
        mock_verify.return_value = True
        payload = {
            'event_type': 'unknown_event',
            'event_data': {}
        }
        
        # Act
        response = self.client.post(self.url, data=payload, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('common.permissions.verify_qstash_signature')
    def test_analytics_event_webhook_invalid_signature(self, mock_verify):
        """Webhook: 無効な署名で401エラー"""
        # Arrange
        mock_verify.return_value = False
        payload = {'event_type': 'auth_event', 'event_data': {}}
        
        # Act
        response = self.client.post(self.url, data=payload, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DltPipelineWebhookTestCase(TestCase):
    """dlt pipeline webhook のテスト"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/webhooks/dlt-pipeline'
    
    @patch('common.permissions.verify_qstash_signature')
    @patch('users.views.subprocess.run')
    def test_dlt_pipeline_webhook_success(self, mock_subprocess, mock_verify):
        """Webhook: パイプライン実行が成功する"""
        # Arrange
        mock_verify.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Pipeline completed successfully"
        mock_subprocess.return_value = mock_result
        
        # Act
        response = self.client.post(self.url, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        mock_subprocess.assert_called_once()
    
    @patch('common.permissions.verify_qstash_signature')
    @patch('users.views.subprocess.run')
    def test_dlt_pipeline_webhook_failure(self, mock_subprocess, mock_verify):
        """Webhook: パイプライン実行が失敗する"""
        # Arrange
        mock_verify.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Pipeline execution failed"
        mock_subprocess.return_value = mock_result
        
        # Act
        response = self.client.post(self.url, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['status'], 'error')
    
    @patch('common.permissions.verify_qstash_signature')
    @patch('users.views.subprocess.run')
    def test_dlt_pipeline_webhook_timeout(self, mock_subprocess, mock_verify):
        """Webhook: パイプライン実行がタイムアウト"""
        # Arrange
        mock_verify.return_value = True
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired('python', 300)
        
        # Act
        response = self.client.post(self.url, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('timeout', response.data['message'].lower())
    
    @patch('common.permissions.verify_qstash_signature')
    def test_dlt_pipeline_webhook_invalid_signature(self, mock_verify):
        """Webhook: 無効な署名で401エラー"""
        # Arrange
        mock_verify.return_value = False
        
        # Act
        response = self.client.post(self.url, format='json')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)