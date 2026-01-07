"""
Tests for UserEmailService
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings

from users.email_service import UserEmailService


class UserEmailServiceTestCase(TestCase):
    """Tests for UserEmailService"""

    def setUp(self):
        self.service = UserEmailService()

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_success(self, mock_send):
        """Test successful welcome email sending"""
        # Arrange
        mock_send.return_value = {"id": "email_welcome_123"}
        email = "newuser@example.com"
        first_name = "John"

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], "email_welcome_123")
        self.assertIsNone(result["error"])
        mock_send.assert_called_once()

        # Verify email parameters
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["to"], [email])
        self.assertIn(first_name, call_args["subject"])
        self.assertIn(first_name, call_args["html"])
        self.assertIn("Welcome", call_args["subject"])

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_contains_dashboard_link(self, mock_send):
        """Test welcome email contains dashboard link"""
        # Arrange
        mock_send.return_value = {"id": "email_123"}
        email = "user@example.com"
        first_name = "Alice"

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        html_content = call_args["html"]
        
        # Verify dashboard link is included
        self.assertIn("https://example.com/dashboard", html_content)
        self.assertIn("Get Started", html_content)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_html_structure(self, mock_send):
        """Test welcome email has proper HTML structure"""
        # Arrange
        mock_send.return_value = {"id": "email_456"}
        email = "test@example.com"
        first_name = "Bob"

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        html_content = call_args["html"]
        
        # Verify HTML structure
        self.assertIn("<html>", html_content)
        self.assertIn("<body", html_content)
        self.assertIn("</body>", html_content)
        self.assertIn("</html>", html_content)
        
        # Verify key elements
        self.assertIn(first_name, html_content)
        self.assertIn("Welcome", html_content)
        self.assertIn("🎉", html_content)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_error(self, mock_send):
        """Test welcome email sending with error"""
        # Arrange
        mock_send.side_effect = Exception("Resend API error")
        email = "user@example.com"
        first_name = "Charlie"

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["id"])
        self.assertIn("Resend API error", result["error"])

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_special_characters_in_name(self, mock_send):
        """Test welcome email with special characters in name"""
        # Arrange
        mock_send.return_value = {"id": "email_789"}
        email = "user@example.com"
        first_name = "François"

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        self.assertIn("François", call_args["subject"])
        self.assertIn("François", call_args["html"])

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_password_reset_email_success(self, mock_send):
        """Test successful password reset email sending"""
        # Arrange
        mock_send.return_value = {"id": "email_reset_123"}
        email = "user@example.com"
        reset_token = "abc123def456"

        # Act
        result = self.service.send_password_reset_email(email, reset_token)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], "email_reset_123")
        mock_send.assert_called_once()

        # Verify email parameters
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["to"], [email])
        self.assertIn("Password Reset", call_args["subject"])

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_password_reset_email_contains_token(self, mock_send):
        """Test password reset email contains reset token in URL"""
        # Arrange
        mock_send.return_value = {"id": "email_456"}
        email = "user@example.com"
        reset_token = "token_xyz_789"

        # Act
        result = self.service.send_password_reset_email(email, reset_token)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        html_content = call_args["html"]
        
        # Verify reset URL with token
        expected_url = f"https://example.com/auth/reset-password?token={reset_token}"
        self.assertIn(expected_url, html_content)
        self.assertIn("Reset Password", html_content)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_password_reset_email_contains_expiration_info(self, mock_send):
        """Test password reset email contains expiration information"""
        # Arrange
        mock_send.return_value = {"id": "email_789"}
        email = "user@example.com"
        reset_token = "token_abc"

        # Act
        result = self.service.send_password_reset_email(email, reset_token)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        html_content = call_args["html"]
        
        # Verify expiration information
        self.assertIn("24 hours", html_content)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_password_reset_email_error(self, mock_send):
        """Test password reset email sending with error"""
        # Arrange
        mock_send.side_effect = Exception("API error")
        email = "user@example.com"
        reset_token = "token_123"

        # Act
        result = self.service.send_password_reset_email(email, reset_token)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["id"])
        self.assertIn("API error", result["error"])

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://production.example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_uses_frontend_url_from_settings(self, mock_send):
        """Test welcome email uses FRONTEND_URL from settings"""
        # Arrange
        mock_send.return_value = {"id": "email_settings_test"}
        email = "user@example.com"
        first_name = "Test"

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        html_content = call_args["html"]
        
        # Verify production URL is used
        self.assertIn("https://production.example.com/dashboard", html_content)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://staging.example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_password_reset_email_uses_frontend_url_from_settings(self, mock_send):
        """Test password reset email uses FRONTEND_URL from settings"""
        # Arrange
        mock_send.return_value = {"id": "email_reset_settings"}
        email = "user@example.com"
        reset_token = "token_123"

        # Act
        result = self.service.send_password_reset_email(email, reset_token)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        html_content = call_args["html"]
        
        # Verify staging URL is used
        self.assertIn("https://staging.example.com/auth/reset-password", html_content)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_empty_name(self, mock_send):
        """Test welcome email with empty name"""
        # Arrange
        mock_send.return_value = {"id": "email_empty_name"}
        email = "user@example.com"
        first_name = ""

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        # Email should still be sent even with empty name
        self.assertIsNotNone(call_args["subject"])
        self.assertIsNotNone(call_args["html"])

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="custom@example.com",
        FRONTEND_URL="https://example.com",
    )
    @patch("common.infrastructure.email_client.resend.Emails.send")
    def test_email_service_uses_default_from_email(self, mock_send):
        """Test that email service uses DEFAULT_FROM_EMAIL from settings"""
        # Arrange
        mock_send.return_value = {"id": "email_from_test"}
        email = "user@example.com"
        first_name = "Test"

        # Act
        result = self.service.send_welcome_email(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["from"], "custom@example.com")