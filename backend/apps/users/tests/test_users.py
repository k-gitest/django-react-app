"""
Tests for users app
Models, Serializers, Services, Views
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status

from apps.users.models import CustomUser, CustomUserManager
from apps.users.serializers import (
    CustomUserSerializer,
    CustomRegisterSerializer,
    CustomLoginSerializer,
    WelcomeEmailWebhookSerializer
)
from apps.users.user_service import (
    UserQueryService,
    UserCommandService,
    UserRegistrationService,
    UserAuthService
)
from apps.users.analytics_service import AnalyticsService
from apps.users.email_service import UserEmailService
from apps.users.qstash_service import UserQStashService
from apps.common.exceptions import (
    UserAlreadyExistsError,
    EmailDeliveryError,
    QStashError,
    AnalyticsError
)


User = get_user_model()


# ================================
# Model Tests
# ================================

class CustomUserModelTestCase(TestCase):
    """Tests for CustomUser model"""

    def test_create_user_with_email(self):
        """Test creating user with email"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating superuser"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        
        self.assertEqual(superuser.email, "admin@example.com")
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_email_normalization(self):
        """Test email normalization"""
        user = User.objects.create_user(
            email="Test@EXAMPLE.com",
            password="pass123"
        )
        
        # Domain should be lowercase
        self.assertEqual(user.email, "Test@example.com")

    def test_email_unique_constraint(self):
        """Test email uniqueness"""
        User.objects.create_user(
            email="unique@example.com",
            password="pass123"
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="unique@example.com",
                password="pass456"
            )

    def test_get_by_natural_key_case_insensitive(self):
        """Test case-insensitive login"""
        User.objects.create_user(
            email="User@Example.com",
            password="pass123"
        )
        
        # Should find user regardless of case
        user = User.objects.get_by_natural_key("user@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "User@example.com")

    def test_str_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        
        self.assertEqual(str(user), "test@example.com")


# ================================
# Serializer Tests
# ================================

class CustomUserSerializerTestCase(TestCase):
    """Tests for CustomUserSerializer"""

    def test_serializer_fields(self):
        """Test serializer contains correct fields"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123",
            first_name="John",
            last_name="Doe"
        )
        
        serializer = CustomUserSerializer(user)
        data = serializer.data
        
        self.assertEqual(set(data.keys()), {'id', 'email', 'first_name', 'last_name', 'is_staff'})
        self.assertEqual(data['email'], "test@example.com")
        self.assertEqual(data['first_name'], "John")
        self.assertEqual(data['last_name'], "Doe")

    def test_read_only_fields(self):
        """Test that id, email, is_staff are read-only"""
        user = User.objects.create_user(email="test@example.com", password="pass123")
        
        serializer = CustomUserSerializer(user, data={
            'id': 999,
            'email': 'hacker@example.com',
            'is_staff': True,
            'first_name': 'Updated'
        })
        
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        user.refresh_from_db()
        # Read-only fields should not be updated
        self.assertNotEqual(user.email, 'hacker@example.com')
        self.assertFalse(user.is_staff)
        # Writable field should be updated
        self.assertEqual(user.first_name, 'Updated')


class CustomRegisterSerializerTestCase(TestCase):
    """Tests for CustomRegisterSerializer"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_valid_registration_data(self):
        """Test serializer with valid data"""
        data = {
            'email': 'newuser@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        serializer = CustomRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Test password mismatch validation"""
        data = {
            'email': 'test@example.com',
            'password1': 'pass123',
            'password2': 'different',
        }
        
        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_invalid_email(self):
        """Test invalid email format"""
        data = {
            'email': 'not-an-email',
            'password1': 'pass123',
            'password2': 'pass123',
        }
        
        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class WelcomeEmailWebhookSerializerTestCase(TestCase):
    """Tests for WelcomeEmailWebhookSerializer"""

    def test_valid_webhook_payload(self):
        """Test valid webhook payload"""
        data = {
            'email': 'user@example.com',
            'first_name': 'John'
        }
        
        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'user@example.com')
        self.assertEqual(serializer.validated_data['first_name'], 'John')

    def test_missing_email(self):
        """Test missing email field"""
        data = {'first_name': 'John'}
        
        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertEqual(serializer.errors['email'][0], 'email is required')

    def test_missing_first_name(self):
        """Test missing first_name field"""
        data = {'email': 'user@example.com'}
        
        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_blank_first_name(self):
        """Test blank first_name"""
        data = {
            'email': 'user@example.com',
            'first_name': ''
        }
        
        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())


# ================================
# Service Tests - UserQueryService
# ================================

class UserQueryServiceTestCase(TestCase):
    """Tests for UserQueryService"""

    def setUp(self):
        self.service = UserQueryService()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )

    def test_get_user_by_email(self):
        """Test getting user by email"""
        user = self.service.get_user_by_email("test@example.com")
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_email_case_insensitive(self):
        """Test case-insensitive email lookup"""
        user = self.service.get_user_by_email("TEST@EXAMPLE.COM")
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_email_not_found(self):
        """Test getting nonexistent user returns None"""
        user = self.service.get_user_by_email("nonexistent@example.com")
        
        self.assertIsNone(user)

    def test_email_exists(self):
        """Test checking if email exists"""
        self.assertTrue(self.service.email_exists("test@example.com"))
        self.assertFalse(self.service.email_exists("nonexistent@example.com"))

    def test_email_exists_case_insensitive(self):
        """Test email_exists is case-insensitive"""
        self.assertTrue(self.service.email_exists("TEST@EXAMPLE.COM"))

    def test_get_user_by_id(self):
        """Test getting user by ID"""
        user = self.service.get_user_by_id(self.user.id)
        
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user.id)

    def test_get_user_by_id_not_found(self):
        """Test getting nonexistent user by ID returns None"""
        user = self.service.get_user_by_id(99999)
        
        self.assertIsNone(user)


# ================================
# Service Tests - UserCommandService
# ================================

class UserCommandServiceTestCase(TestCase):
    """Tests for UserCommandService"""

    def setUp(self):
        self.service = UserCommandService()
        self.factory = RequestFactory()

    def test_create_user(self):
        """Test creating user"""
        user = self.service.create_user(
            email="newuser@example.com",
            password="pass123",
            first_name="John",
            last_name="Doe"
        )
        
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("pass123"))

    def test_create_user_with_adapter(self):
        """Test creating user with allauth adapter"""
        request = self.factory.post('/register')
        
        user = self.service.create_user_with_adapter(
            request=request,
            email="adapter@example.com",
            password="pass123",
            first_name="Jane",
            last_name="Smith"
        )
        
        self.assertEqual(user.email, "adapter@example.com")
        self.assertEqual(user.first_name, "Jane")

    def test_update_user(self):
        """Test updating user"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        
        updated = self.service.update_user(
            user,
            first_name="Updated",
            last_name="Name"
        )
        
        self.assertEqual(updated.first_name, "Updated")
        self.assertEqual(updated.last_name, "Name")

    def test_change_password(self):
        """Test changing password"""
        user = User.objects.create_user(
            email="test@example.com",
            password="oldpass"
        )
        
        updated = self.service.change_password(user, "newpass")
        
        self.assertTrue(updated.check_password("newpass"))
        self.assertFalse(updated.check_password("oldpass"))

    def test_delete_user(self):
        """Test deleting user"""
        user = User.objects.create_user(
            email="delete@example.com",
            password="pass123"
        )
        user_id = user.id
        
        self.service.delete_user(user)
        
        self.assertFalse(User.objects.filter(id=user_id).exists())


# ================================
# Service Tests - UserRegistrationService
# ================================

class UserRegistrationServiceTestCase(TestCase):
    """Tests for UserRegistrationService"""

    def setUp(self):
        self.service = UserRegistrationService()
        self.factory = RequestFactory()

    @override_settings(TESTING=True)
    def test_register_user_success(self):
        """Test successful user registration"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'newuser@example.com',
            'password': 'pass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        user = self.service.register_user(request, user_data)
        
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertTrue(user.check_password('pass123'))

    @override_settings(TESTING=True)
    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email raises UserAlreadyExistsError"""
        User.objects.create_user(
            email="duplicate@example.com",
            password="pass123"
        )
        
        request = self.factory.post('/register')
        user_data = {
            'email': 'duplicate@example.com',
            'password': 'pass456'
        }
        
        with self.assertRaises(UserAlreadyExistsError) as context:
            self.service.register_user(request, user_data)
        
        self.assertIn("duplicate@example.com", str(context.exception))

    @override_settings(TESTING=True)
    def test_register_user_case_insensitive_duplicate(self):
        """Test duplicate check is case-insensitive"""
        User.objects.create_user(
            email="case@example.com",
            password="pass123"
        )
        
        request = self.factory.post('/register')
        user_data = {
            'email': 'CASE@EXAMPLE.COM',
            'password': 'pass456'
        }
        
        with self.assertRaises(UserAlreadyExistsError):
            self.service.register_user(request, user_data)


# ================================
# Service Tests - AnalyticsService
# ================================

class AnalyticsServiceTestCase(TestCase):
    """Tests for AnalyticsService"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        # シングルトンをリセット
        AnalyticsService._client = None

    def tearDown(self):
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        AnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_auth_event_login(self, mock_setup_schema, mock_connect):
        """Test logging login event"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        request = self.factory.post('/login')
        
        result = AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )
        
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_auth_event_with_ip_address(self, mock_setup_schema, mock_connect):
        """Test IP address extraction"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        request = self.factory.post('/login', REMOTE_ADDR="192.168.1.1")
        
        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )
        
        # Verify execute was called with IP address
        call_args = mock_conn.execute.call_args
        self.assertIsNotNone(call_args)

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_auth_event_with_x_forwarded_for(self, mock_setup_schema, mock_connect):
        """Test X-Forwarded-For header handling"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        request = self.factory.post(
            '/login',
            HTTP_X_FORWARDED_FOR="203.0.113.1, 198.51.100.1"
        )
        
        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )
        
        mock_conn.execute.assert_called_once()


# ================================
# Service Tests - UserEmailService
# ================================

class UserEmailServiceTestCase(TestCase):
    """Tests for UserEmailService"""

    def setUp(self):
        UserEmailService._client = None

    def tearDown(self):
        UserEmailService._client = None

    @override_settings(
        RESEND_API_KEY="test_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com"
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_success(self, mock_send):
        """Test sending welcome email"""
        mock_send.return_value = {"id": "email_123"}
        
        message_id = UserEmailService.send_welcome_email(
            "user@example.com",
            "John"
        )
        
        self.assertEqual(message_id, "email_123")
        mock_send.assert_called_once()
        
        # Verify email content
        call_args = mock_send.call_args[0][0]
        self.assertIn("John", call_args["subject"])
        self.assertIn("John", call_args["html"])
        self.assertIn("https://example.com/dashboard", call_args["html"])

    @override_settings(
        RESEND_API_KEY="test_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com"
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_password_reset_email(self, mock_send):
        """Test sending password reset email"""
        mock_send.return_value = {"id": "email_456"}
        
        message_id = UserEmailService.send_password_reset_email(
            "user@example.com",
            "reset_token_123"
        )
        
        self.assertEqual(message_id, "email_456")
        
        # Verify reset URL in email
        call_args = mock_send.call_args[0][0]
        self.assertIn("reset_token_123", call_args["html"])
        self.assertIn("/auth/reset-password", call_args["html"])


# ================================
# Service Tests - UserQStashService
# ================================

class UserQStashServiceTestCase(TestCase):
    """Tests for UserQStashService"""

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_success(self, mock_post):
        """Test queueing welcome email"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        message_id = UserQStashService.send_welcome_email_async(
            "user@example.com",
            "John"
        )
        
        self.assertEqual(message_id, "msg_123")
        mock_post.assert_called_once()
        
        # Verify payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["email"], "user@example.com")
        self.assertEqual(payload["first_name"], "John")


# ================================
# View Tests
# ================================

class AuthenticationViewsTestCase(APITestCase):
    """Tests for authentication views"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John"
        )

    @override_settings(TESTING=True)
    @patch("apps.users.views.UserAuthService.handle_login_success")
    def test_login_success(self, mock_handle_login):
        """Test successful login"""
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "email": "test@example.com",
                "password": "testpass123"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        
        # Verify analytics was called
        mock_handle_login.assert_called_once()

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "email": "test@example.com",
                "password": "wrongpass"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(TESTING=True)
    def test_register_success(self):
        """Test successful registration"""
        response = self.client.post(
            "/api/v1/auth/registration/",
            {
                "email": "newuser@example.com",
                "password1": "newpass123",
                "password2": "newpass123",
                "first_name": "Jane"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email="newuser@example.com").exists()
        )

    @override_settings(TESTING=True)
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        response = self.client.post(
            "/api/v1/auth/registration/",
            {
                "email": "test@example.com",  # Already exists
                "password1": "newpass123",
                "password2": "newpass123"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class WelcomeEmailWebhookViewTestCase(APITestCase):
    """Tests for send_welcome_email_webhook view"""

    @patch("apps.users.views.UserEmailService.send_welcome_email")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_success(self, mock_verify_signature, mock_send_email):
        """Test successful webhook call"""
        mock_verify_signature.return_value = True
        mock_send_email.return_value = "email_123"
        
        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {
                "email": "user@example.com",
                "first_name": "John"
            },
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message_id"], "email_123")
        mock_send_email.assert_called_once_with("user@example.com", "John")

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_invalid_signature(self, mock_verify_signature):
        """Test webhook with invalid signature"""
        mock_verify_signature.return_value = False
        
        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {
                "email": "user@example.com",
                "first_name": "John"
            },
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_missing_fields(self, mock_verify_signature):
        """Test webhook with missing required fields"""
        mock_verify_signature.return_value = True
        
        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {"email": "user@example.com"},  # Missing first_name
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)