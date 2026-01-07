"""
Tests for User Service Layer
"""
from django.test import TestCase, RequestFactory
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from users.user_service import (
    UserQueryService,
    UserCommandService,
    UserRegistrationService,
)

User = get_user_model()


class UserQueryServiceTestCase(TestCase):
    """Tests for UserQueryService"""

    def setUp(self):
        self.service = UserQueryService()
        self.test_user = User.objects.create_user(
            email="existing@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )

    def test_get_user_by_email_success(self):
        """Test successfully getting user by email"""
        user = self.service.get_user_by_email("existing@example.com")
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "existing@example.com")
        self.assertEqual(user.first_name, "John")

    def test_get_user_by_email_case_insensitive(self):
        """Test email lookup is case-insensitive"""
        user = self.service.get_user_by_email("EXISTING@EXAMPLE.COM")
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "existing@example.com")

    def test_get_user_by_email_not_found(self):
        """Test getting user with non-existent email returns None"""
        user = self.service.get_user_by_email("nonexistent@example.com")
        
        self.assertIsNone(user)

    def test_email_exists_true(self):
        """Test email_exists returns True for existing email"""
        exists = self.service.email_exists("existing@example.com")
        
        self.assertTrue(exists)

    def test_email_exists_case_insensitive(self):
        """Test email_exists is case-insensitive"""
        exists = self.service.email_exists("EXISTING@EXAMPLE.COM")
        
        self.assertTrue(exists)

    def test_email_exists_false(self):
        """Test email_exists returns False for non-existent email"""
        exists = self.service.email_exists("nonexistent@example.com")
        
        self.assertFalse(exists)

    def test_get_user_by_id_success(self):
        """Test successfully getting user by ID"""
        user = self.service.get_user_by_id(self.test_user.id)
        
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.test_user.id)
        self.assertEqual(user.email, "existing@example.com")

    def test_get_user_by_id_not_found(self):
        """Test getting user with non-existent ID returns None"""
        user = self.service.get_user_by_id(99999)
        
        self.assertIsNone(user)


class UserCommandServiceTestCase(TestCase):
    """Tests for UserCommandService"""

    def setUp(self):
        self.service = UserCommandService()

    def test_create_user_success(self):
        """Test successfully creating a user"""
        user = self.service.create_user(
            email="newuser@example.com",
            password="testpass123",
            first_name="Alice",
            last_name="Smith"
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "Alice")
        self.assertEqual(user.last_name, "Smith")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_user_minimal_data(self):
        """Test creating user with minimal required data"""
        user = self.service.create_user(
            email="minimal@example.com",
            password="testpass123"
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "minimal@example.com")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")

    def test_create_user_with_extra_fields(self):
        """Test creating user with extra fields"""
        user = self.service.create_user(
            email="extra@example.com",
            password="testpass123",
            is_staff=True
        )
        
        self.assertTrue(user.is_staff)

    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email raises IntegrityError"""
        # Create first user
        self.service.create_user(
            email="duplicate@example.com",
            password="testpass123"
        )
        
        # Attempt to create second user with same email
        with self.assertRaises(IntegrityError):
            self.service.create_user(
                email="duplicate@example.com",
                password="testpass456"
            )

    def test_create_user_password_is_hashed(self):
        """Test that password is properly hashed"""
        password = "testpass123"
        user = self.service.create_user(
            email="hashed@example.com",
            password=password
        )
        
        # Password should not be stored in plain text
        self.assertNotEqual(user.password, password)
        # But check_password should work
        self.assertTrue(user.check_password(password))

    def test_create_user_with_adapter_success(self):
        """Test creating user with adapter"""
        from django.test import RequestFactory
        
        request = RequestFactory().post('/register')
        user = self.service.create_user_with_adapter(
            request=request,
            email="adapter@example.com",
            password="testpass123",
            first_name="Bob",
            last_name="Johnson"
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "adapter@example.com")
        self.assertEqual(user.first_name, "Bob")
        self.assertEqual(user.last_name, "Johnson")

    def test_create_user_with_adapter_duplicate_email(self):
        """Test creating user with adapter raises IntegrityError for duplicate email"""
        from django.test import RequestFactory
        
        request = RequestFactory().post('/register')
        
        # Create first user
        self.service.create_user_with_adapter(
            request=request,
            email="duplicate@example.com",
            password="testpass123"
        )
        
        # Attempt to create second user with same email
        with self.assertRaises(IntegrityError):
            self.service.create_user_with_adapter(
                request=request,
                email="duplicate@example.com",
                password="testpass456"
            )

    def test_update_user_success(self):
        """Test successfully updating user"""
        user = User.objects.create_user(
            email="update@example.com",
            password="testpass123"
        )
        
        updated_user = self.service.update_user(
            user,
            first_name="Updated",
            last_name="Name"
        )
        
        self.assertEqual(updated_user.first_name, "Updated")
        self.assertEqual(updated_user.last_name, "Name")
        
        # Verify changes persisted to database
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Updated")

    def test_update_user_multiple_fields(self):
        """Test updating multiple fields at once"""
        user = User.objects.create_user(
            email="multi@example.com",
            password="testpass123"
        )
        
        updated_user = self.service.update_user(
            user,
            first_name="Multi",
            last_name="Field",
            is_staff=True
        )
        
        self.assertEqual(updated_user.first_name, "Multi")
        self.assertEqual(updated_user.last_name, "Field")
        self.assertTrue(updated_user.is_staff)

    def test_update_user_invalid_field_ignored(self):
        """Test that invalid fields are ignored during update"""
        user = User.objects.create_user(
            email="invalid@example.com",
            password="testpass123"
        )
        
        # Should not raise error, just ignore invalid field
        updated_user = self.service.update_user(
            user,
            first_name="Valid",
            invalid_field="Should be ignored"
        )
        
        self.assertEqual(updated_user.first_name, "Valid")
        self.assertFalse(hasattr(updated_user, 'invalid_field'))

    def test_change_password_success(self):
        """Test successfully changing password"""
        user = User.objects.create_user(
            email="password@example.com",
            password="oldpass123"
        )
        
        # Verify old password works
        self.assertTrue(user.check_password("oldpass123"))
        
        # Change password
        updated_user = self.service.change_password(user, "newpass456")
        
        # Verify new password works and old doesn't
        self.assertTrue(updated_user.check_password("newpass456"))
        self.assertFalse(updated_user.check_password("oldpass123"))

    def test_change_password_persists(self):
        """Test password change persists to database"""
        user = User.objects.create_user(
            email="persist@example.com",
            password="oldpass123"
        )
        
        self.service.change_password(user, "newpass456")
        
        # Refresh from database and verify
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass456"))

    def test_delete_user_success(self):
        """Test successfully deleting user"""
        user = User.objects.create_user(
            email="delete@example.com",
            password="testpass123"
        )
        user_id = user.id
        
        self.service.delete_user(user)
        
        # Verify user no longer exists
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_user_cascades(self):
        """Test deleting user cascades to related objects"""
        from todos.models import Todo
        
        user = User.objects.create_user(
            email="cascade@example.com",
            password="testpass123"
        )
        
        # Create related todo
        todo = Todo.objects.create(
            user=user,
            todo_title="Test Todo"
        )
        todo_id = todo.id
        
        # Delete user
        self.service.delete_user(user)
        
        # Verify todo was also deleted (cascade)
        self.assertFalse(Todo.objects.filter(id=todo_id).exists())


class UserRegistrationServiceTestCase(TestCase):
    """Tests for UserRegistrationService"""

    def setUp(self):
        self.service = UserRegistrationService()
        self.factory = RequestFactory()

    def test_register_user_success(self):
        """Test successfully registering a new user"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'register@example.com',
            'password': 'testpass123',
            'first_name': 'Register',
            'last_name': 'Test'
        }
        
        user = self.service.register_user(request, user_data)
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'register@example.com')
        self.assertEqual(user.first_name, 'Register')
        self.assertEqual(user.last_name, 'Test')
        self.assertTrue(user.check_password('testpass123'))

    def test_register_user_minimal_data(self):
        """Test registering user with minimal required data"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'minimal@example.com',
            'password': 'testpass123'
        }
        
        user = self.service.register_user(request, user_data)
        
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'minimal@example.com')
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')

    def test_register_user_duplicate_email(self):
        """Test registering user with duplicate email raises ValueError"""
        request = self.factory.post('/register')
        
        # Create first user
        User.objects.create_user(
            email='duplicate@example.com',
            password='testpass123'
        )
        
        # Attempt to register with same email
        user_data = {
            'email': 'duplicate@example.com',
            'password': 'testpass456'
        }
        
        with self.assertRaises(ValueError) as context:
            self.service.register_user(request, user_data)
        
        self.assertIn('already registered', str(context.exception))

    def test_register_user_duplicate_email_case_insensitive(self):
        """Test duplicate email check is case-insensitive"""
        request = self.factory.post('/register')
        
        # Create first user
        User.objects.create_user(
            email='case@example.com',
            password='testpass123'
        )
        
        # Attempt to register with same email (different case)
        user_data = {
            'email': 'CASE@EXAMPLE.COM',
            'password': 'testpass456'
        }
        
        with self.assertRaises(ValueError):
            self.service.register_user(request, user_data)

    def test_register_user_with_optional_fields(self):
        """Test registering user with all optional fields"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'optional@example.com',
            'password': 'testpass123',
            'first_name': 'Optional',
            'last_name': 'Fields'
        }
        
        user = self.service.register_user(request, user_data)
        
        self.assertEqual(user.first_name, 'Optional')
        self.assertEqual(user.last_name, 'Fields')

    def test_register_user_creates_in_database(self):
        """Test that registered user is actually created in database"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'database@example.com',
            'password': 'testpass123'
        }
        
        user = self.service.register_user(request, user_data)
        
        # Verify user exists in database
        self.assertTrue(User.objects.filter(id=user.id).exists())
        db_user = User.objects.get(id=user.id)
        self.assertEqual(db_user.email, 'database@example.com')

    def test_register_user_uses_query_service(self):
        """Test that registration service uses query service for duplicate check"""
        request = self.factory.post('/register')
        
        # Create existing user
        User.objects.create_user(
            email='existing@example.com',
            password='testpass123'
        )
        
        # Attempt to register with same email
        user_data = {
            'email': 'existing@example.com',
            'password': 'testpass456'
        }
        
        # Should use query_service.email_exists() and raise ValueError
        with self.assertRaises(ValueError):
            self.service.register_user(request, user_data)

    def test_register_user_uses_command_service(self):
        """Test that registration service uses command service to create user"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'command@example.com',
            'password': 'testpass123',
            'first_name': 'Command',
            'last_name': 'Service'
        }
        
        # Should use command_service.create_user_with_adapter()
        user = self.service.register_user(request, user_data)
        
        self.assertIsNotNone(user)
        # Verify user was created correctly
        self.assertEqual(user.email, 'command@example.com')

    def test_register_user_password_not_stored_plaintext(self):
        """Test that password is not stored in plaintext"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'secure@example.com',
            'password': 'testpass123'
        }
        
        user = self.service.register_user(request, user_data)
        
        # Password should be hashed
        self.assertNotEqual(user.password, 'testpass123')
        # But should verify correctly
        self.assertTrue(user.check_password('testpass123'))


class UserServiceIntegrationTestCase(TestCase):
    """Integration tests for user services working together"""

    def setUp(self):
        self.query_service = UserQueryService()
        self.command_service = UserCommandService()
        self.registration_service = UserRegistrationService()
        self.factory = RequestFactory()

    def test_register_and_query_flow(self):
        """Test complete flow of registering and querying a user"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'flow@example.com',
            'password': 'testpass123',
            'first_name': 'Flow',
            'last_name': 'Test'
        }
        
        # Register user
        registered_user = self.registration_service.register_user(request, user_data)
        
        # Query by email
        queried_user = self.query_service.get_user_by_email('flow@example.com')
        self.assertEqual(registered_user.id, queried_user.id)
        
        # Query by ID
        queried_by_id = self.query_service.get_user_by_id(registered_user.id)
        self.assertEqual(registered_user.id, queried_by_id.id)
        
        # Check existence
        exists = self.query_service.email_exists('flow@example.com')
        self.assertTrue(exists)

    def test_create_update_delete_flow(self):
        """Test complete CRUD flow"""
        # Create
        user = self.command_service.create_user(
            email='crud@example.com',
            password='testpass123'
        )
        self.assertIsNotNone(user.id)
        
        # Read/Query
        found_user = self.query_service.get_user_by_id(user.id)
        self.assertEqual(found_user.email, 'crud@example.com')
        
        # Update
        updated_user = self.command_service.update_user(
            user,
            first_name='Updated',
            last_name='User'
        )
        self.assertEqual(updated_user.first_name, 'Updated')
        
        # Delete
        self.command_service.delete_user(user)
        deleted_user = self.query_service.get_user_by_id(user.id)
        self.assertIsNone(deleted_user)