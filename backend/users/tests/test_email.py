from django.test import TestCase
from unittest.mock import patch, MagicMock
from users.email_service import EmailService
from users.qstash_service import QStashService


class EmailServiceTest(TestCase):
    
    @patch('resend.Emails.send')
    def test_send_welcome_email_success(self, mock_send):
        """ウェルカムメール送信が成功する"""
        mock_send.return_value = {"id": "test-email-id"}
        
        result = EmailService.send_welcome_email(
            email="test@example.com",
            first_name="Test"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], "test-email-id")
        mock_send.assert_called_once()


class QStashServiceTest(TestCase):
    
    @patch('requests.post')
    def test_send_welcome_email_async_success(self, mock_post):
        """QStashへのメッセージ送信が成功する"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "test-message-id"}
        mock_post.return_value = mock_response
        
        result = QStashService.send_welcome_email_async(
            email="test@example.com",
            first_name="Test"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "test-message-id")