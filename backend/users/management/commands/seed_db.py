from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import User

class Command(BaseCommand):
    help = 'Seed database with test data'

    def handle(self, *args, **options):
        # E2Eテスト用ユーザー
        test_email = getattr(settings, 'E2E_TEST_EMAIL', 'e2e-test@example.com')
        test_password = getattr(settings, 'E2E_TEST_PASSWORD', 'TestPassword123!')
        
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={
                'first_name': 'E2E',
                'last_name': 'Tester',
                'is_active': True,
            }
        )
        
        if created:
            user.set_password(test_password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✅ E2E test user created: {test_email}'))
        else:
            # パスワードを確実に設定（既存ユーザーの場合）
            user.set_password(test_password)
            user.save()
            self.stdout.write(self.style.WARNING(f'⚠️ E2E test user already exists: {test_email}'))