import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Resendを使ったメール送信サービス"""
    
    @staticmethod
    def send_welcome_email(email: str, first_name: str):
        """ウェルカムメール送信"""
        try:
            params = {
                "from": "noreply@yourdomain.com",  # 検証済みドメイン
                "to": [email],
                "subject": f"Welcome to Django React App, {first_name}!",
                "html": f"""
                <html>
                    <body>
                        <h1>Welcome, {first_name}!</h1>
                        <p>Thank you for registering with Django React App.</p>
                        <p>We're excited to have you on board!</p>
                        <p>
                            <a href="{settings.FRONTEND_URL}/dashboard">
                                Get Started
                            </a>
                        </p>
                    </body>
                </html>
                """
            }
            
            response = resend.Emails.send(params)
            return {"success": True, "id": response["id"]}
            
        except Exception as e:
            # ログに記録（本番環境ではSentryなどに送信）
            print(f"Failed to send email: {str(e)}")
            return {"success": False, "error": str(e)}