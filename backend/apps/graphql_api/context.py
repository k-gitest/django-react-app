from dataclasses import dataclass
from django.http import HttpRequest

@dataclass
class Context:
    """GraphQLの全リゾーバで共有されるデータ"""
    request: HttpRequest

def get_context(request: HttpRequest) -> Context:
    """DjangoのリクエストをContextオブジェクトに包んで返す"""
    return Context(request=request)