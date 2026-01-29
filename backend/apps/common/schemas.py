from drf_spectacular.utils import OpenApiExample

class CommonSchemas:
    """共通のスキーマ定義"""
    
    # エラーレスポンス
    ERROR_400 = OpenApiExample(
        'Bad Request',
        value={
            'error': 'validation_error',
            'detail': 'リクエストデータが不正です',
            'data': {
                'field_name': ['エラーメッセージ']
            }
        },
        response_only=True,
    )
    
    ERROR_401 = OpenApiExample(
        'Unauthorized',
        value={
            'error': 'authentication_failed',
            'detail': '認証情報が提供されていません。'
        },
        response_only=True,
    )
    
    ERROR_403 = OpenApiExample(
        'Forbidden',
        value={
            'error': 'permission_denied',
            'detail': 'この操作を実行する権限がありません。'
        },
        response_only=True,
    )
    
    ERROR_404 = OpenApiExample(
        'Not Found',
        value={
            'error': 'not_found',
            'detail': 'リソースが見つかりません。'
        },
        response_only=True,
    )
    
    ERROR_429 = OpenApiExample(
        'Too Many Requests',
        value={
            'detail': 'リクエストが多すぎます。しばらく時間を置いてから再度お試しください。'
        },
        response_only=True,
    )
    
    ERROR_500 = OpenApiExample(
        'Internal Server Error',
        value={
            'error': 'internal_error',
            'detail': 'サーバーエラーが発生しました。'
        },
        response_only=True,
    )
    
    # よく使うレスポンス定義
    COMMON_RESPONSES = {
        401: ERROR_401,
        403: ERROR_403,
        404: ERROR_404,
        429: ERROR_429,
        500: ERROR_500,
    }