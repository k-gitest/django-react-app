from django.test import TestCase
from unittest.mock import patch, MagicMock
from users.email_service import UserEmailService
from users.qstash_service import UserQStashService


class EmailServiceTest(TestCase):
    
    @patch('common.infrastructure.email_client.resend.Emails.send')
    def test_send_welcome_email_success(self, mock_send):
        """ウェルカムメール送信が成功する"""
        mock_send.return_value = {"id": "test-email-id"}
        
        # インスタンスを作成してから呼び出す
        service = UserEmailService()
        result = service.send_welcome_email(
            email="test@example.com",
            first_name="Test"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], "test-email-id")
        mock_send.assert_called_once()


class QStashServiceTest(TestCase):
    
    @patch('common.infrastructure.qstash_client.requests.post')
    def test_send_welcome_email_async_success(self, mock_post):
        """QStashへのメッセージ送信が成功する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "test-message-id"}
        mock_response.raise_for_status = MagicMock()  # 追加
        mock_post.return_value = mock_response
        
        result = UserQStashService.send_welcome_email_async(
            email="test@example.com",
            first_name="Test"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "test-message-id")