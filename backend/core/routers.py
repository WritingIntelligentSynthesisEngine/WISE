# core/routers.py
from typing import Any

from ninja import Router

router: Router = Router(tags=["测试"])


@router.get(
    "/hello",
    summary="连通测试",
)
def hello(request: Any) -> str:
    """用于连通测试, 返回一个字符串"""
    return "Hello World!"
