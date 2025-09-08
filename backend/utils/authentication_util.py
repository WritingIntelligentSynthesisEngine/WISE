# utils/authentication.py
from typing import Any

from django.http import HttpRequest
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth.models import AnonymousUser


anonymou_suser: AnonymousUser = AnonymousUser()


class OptionalAuth(JWTAuth):
    """一个可选的认证类, 允许匿名访问但也能识别已认证用户"""

    def __call__(self, request: HttpRequest) -> Any:
        auth_result = super().__call__(request)
        if auth_result is None:
            # 如果没有认证信息, 返回匿名用户
            return anonymou_suser
        return auth_result
