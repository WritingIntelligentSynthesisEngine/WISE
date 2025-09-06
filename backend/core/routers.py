# core/routers.py
from typing import Any

from ninja import Router
from django.http import HttpRequest
from ninja_jwt.settings import api_settings
from ninja_extra.permissions import AllowAny
from ninja_jwt.schema_control import SchemaControl
from ninja_extra import ControllerBase, api_controller, http_post
from ninja_jwt.schema import TokenVerifyInputSchema, TokenObtainPairInputSchema, TokenRefreshInputSchema


router: Router = Router(tags=["核心"])

schema = SchemaControl(api_settings)


@router.get(
    "/hello",
    summary="连通测试",
)
def hello(request: HttpRequest) -> str:
    """用于连通测试, 返回一个字符串"""
    return "Hello AllBookCloud!"


class TokenVerificationController:
    auto_import = False

    @http_post(
        "/verify",
        summary="验证令牌",
        response={200: schema.verify_schema.get_response_schema()},
        url_name="token_verify",
        operation_id="token_verify",
    )
    def verify_token(self, token: TokenVerifyInputSchema) -> Any:
        return token.to_response_schema()


class TokenObtainPairController:
    auto_import = False

    @http_post(
        "/pair",
        summary="获取令牌",
        response=schema.obtain_pair_schema.get_response_schema(),
        url_name="token_obtain_pair",
        operation_id="token_obtain_pair",
    )
    def obtain_token(self, user_token: TokenObtainPairInputSchema) -> Any:
        user_token.check_user_authentication_rule()
        return user_token.to_response_schema()

    @http_post(
        "/refresh",
        summary="刷新令牌",
        response=schema.obtain_pair_refresh_schema.get_response_schema(),
        url_name="token_refresh",
        operation_id="token_refresh",
    )
    def refresh_token(self, refresh_token: TokenRefreshInputSchema) -> Any:
        return refresh_token.to_response_schema()


@api_controller("/token", permissions=[AllowAny], tags=["令牌"], auth=None)
class NinjaJWTDefaultController(ControllerBase, TokenVerificationController, TokenObtainPairController):
    """NinjaJWT 获取和刷新令牌的默认控制器"""

    auto_import = False
