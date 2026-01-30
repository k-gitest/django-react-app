from dataclasses import dataclass
from django.http import HttpRequest, HttpResponse


@dataclass
class Context:
    """
    GraphQLの全リゾーバで共有されるデータ
    
    Attributes:
        request: Django HTTPリクエスト
        response: Django HTTPレスポンス（Cookie設定用）
    """
    request: HttpRequest
    response: HttpResponse


def get_context(request: HttpRequest, response: HttpResponse) -> Context:
    """
    DjangoのリクエストとレスポンスをContextオブジェクトに包んで返す
    
    Args:
        request: HTTPリクエストオブジェクト
        response: HTTPレスポンスオブジェクト
    
    Returns:
        Context インスタンス
    """
    return Context(request=request, response=response)