from django.test import TestCase
from django.contrib.auth import get_user_model
from users.serializers import (
    CustomUserSerializer,
    CustomRegisterSerializer,
)

User = get_user_model()


class CustomUserSerializerTest(TestCase):
    """
    CustomUserSerializer のテスト
    """

    def test_serializer_with_valid_data(self):
        """
        正しいデータでシリアライザが動作することを確認
        """
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )

        serializer = CustomUserSerializer(user)
        data = serializer.data

        self.assertEqual(data['email'], "test@example.com")
        self.assertEqual(data['first_name'], "John")
        self.assertEqual(data['last_name'], "Doe")
        self.assertIn('id', data)
        self.assertIn('is_staff', data)

    def test_serializer_does_not_expose_password(self):
        """
        シリアライザがパスワードを公開しないことを確認
        """
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

        serializer = CustomUserSerializer(user)
        data = serializer.data

        self.assertNotIn('password', data)

    def test_serializer_readonly_fields(self):
        """
        読み取り専用フィールドを確認
        """
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

        serializer = CustomUserSerializer(
            user,
            data={
                'id': 999,  # 変更を試みる
                'email': 'newemail@example.com',  # 変更を試みる
                'is_staff': True,  # 変更を試みる
                'first_name': 'Jane',
            },
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # 読み取り専用フィールドは変更されない
        self.assertNotEqual(updated_user.id, 999)
        self.assertEqual(updated_user.email, "test@example.com")
        self.assertFalse(updated_user.is_staff)

        # 編集可能なフィールドは変更される
        self.assertEqual(updated_user.first_name, "Jane")


class CustomRegisterSerializerTest(TestCase):
    """
    CustomRegisterSerializer のテスト
    """

    def test_register_serializer_with_valid_data(self):
        """
        正しいデータで登録シリアライザが動作することを確認
        """
        data = {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_register_serializer_password_mismatch(self):
        """
        パスワードが一致しない場合にエラーが発生することを確認
        """
        data = {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'different456',
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_register_serializer_invalid_email(self):
        """
        無効なメールアドレスでエラーが発生することを確認
        """
        data = {
            'email': 'invalid-email',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_register_serializer_missing_email(self):
        """
        メールアドレスが欠けている場合にエラーが発生することを確認
        """
        data = {
            'password1': 'testpass123',
            'password2': 'testpass123',
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_register_serializer_does_not_have_username_field(self):
        """
        usernameフィールドが存在しないことを確認
        """
        serializer = CustomRegisterSerializer()
        self.assertIsNone(serializer.fields.get('username'))

    def test_register_serializer_optional_name_fields(self):
        """
        first_nameとlast_nameが任意であることを確認
        """
        data = {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())