from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory, override_settings
from rest_framework.test import APIRequestFactory
from apps.common.security import verify_qstash_signature
from apps.common.permissions import IsQStashAuthenticated

class QStashSecurityTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(QSTASH_CURRENT_SIGNING_KEY="cur", QSTASH_NEXT_SIGNING_KEY="nxt")
    @patch("apps.common.security.Receiver")
    def test_verify_signature_success(self, mock_receiver_class):
        """
        [セキュリティ] Upstash QStashからの署名が正しい場合に検証をパスすることを確認
        """
        mock_receiver = MagicMock()
        mock_receiver.verify.return_value = None # verifyメソッドが例外を投げなければ成功
        mock_receiver_class.return_value = mock_receiver
        
        request = self.factory.post("/webhook", HTTP_UPSTASH_SIGNATURE="v1=valid")
        self.assertTrue(verify_qstash_signature(request))

class IsQStashAuthenticatedTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsQStashAuthenticated()

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_permission_granted(self, mock_verify):
        """
        [パーミッション] QStashの署名検証が成功した際に、APIへのアクセスが許可されることを確認
        """
        mock_verify.return_value = True
        request = self.factory.post("/webhook")
        self.assertTrue(self.permission.has_permission(request, None))