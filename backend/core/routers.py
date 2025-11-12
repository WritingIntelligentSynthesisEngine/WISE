# core/routers.py
from ninja import Router
from django.http import HttpRequest
from ninja_jwt.settings import api_settings
from ninja_jwt.schema_control import SchemaControl


router: Router = Router(tags=["核心"])

schema = SchemaControl(api_settings)


@router.get(
    "/hello",
    summary="连通测试",
)
def hello(request: HttpRequest) -> str:
    """用于连通测试, 返回一个字符串"""
    return "Hello WISE!"
