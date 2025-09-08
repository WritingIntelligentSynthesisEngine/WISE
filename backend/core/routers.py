# core/routers.py
from ninja import Router
from django.http import HttpRequest


router: Router = Router(tags=["核心"])


@router.get(
    "/hello",
    summary="连通测试",
)
def hello(request: HttpRequest) -> str:
    """用于连通测试, 返回一个字符串"""
    return "Hello World!"
