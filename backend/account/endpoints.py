# account/endpoints.py
from typing import List, Tuple, Literal

from ninja import Router
from django.http import HttpRequest
from django.utils.encoding import force_str
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db.models.manager import BaseManager
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import AbstractUser

from core.schemas import OutSchema
from utils.exception_util import Error
from account.services import AccountService
from utils.authentication_util import OptionalAuth
from account.schemas import (
    RegisterInSchema,
    AccountOutSchema,
    SensitiveAccountOutSchema,
    EmailRequestInSchema,
    LoginInSchema,
    JwtOutSchema,
    PasswordResetConfirmInSchema,
    AccountUpdateInSchema,
)


User: type[AbstractUser] = get_user_model()

router: Router = Router(tags=["账户"])


@router.post(
    "/accounts",
    summary="注册账户",
    response={201: OutSchema[AccountOutSchema]},
)
def register(
    request: HttpRequest,
    data: RegisterInSchema,
) -> Tuple[Literal[201], OutSchema[AccountOutSchema]]:
    """注册账户, 如果用户已存在但未激活, 则更新用户信息"""

    user: AbstractUser | None = User.objects.filter(email=data.email).first()
    if user:
        # 检查邮箱是否已被占用
        if user.is_active:
            raise Error(400, "email", "邮箱已被注册")
        # 更新未激活账户
        if User.objects.filter(username=data.username).exclude(pk=user.pk).exists():
            raise Error(400, "username", "用户名已被其他账户占用")
    else:
        # 全新注册
        if User.objects.filter(username=data.username).exists():
            raise Error(400, "username", "用户名已存在")
    account: AbstractUser = AccountService.register(user, data)
    return 201, OutSchema(data=AccountOutSchema.model_validate(account))


@router.post(
    "/account-verifications",
    summary="请求验证账户",
    response={201: OutSchema[str]},
)
def account_verify_request(
    request: HttpRequest,
    data: EmailRequestInSchema,
) -> Tuple[Literal[201], OutSchema[str]]:
    """请求验证账户"""

    try:
        user: AbstractUser | None = User.objects.filter(email=data.email).first()
        if user is None:
            # 为了安全不管邮箱存不存在都成功返回
            pass
        else:
            # 检查邮箱是否已被注册且已激活
            if user.is_active:
                raise Error(409, "email", "邮箱已被注册")
            AccountService.account_verify_request(user, data)
    except Exception:
        raise Error(500, "email", "邮件发送失败, 请稍后重试")
    return 201, OutSchema(data="如果邮箱存在, 验证邮件已发送")


@router.put(
    "/account-verifications/{uidb64}/{token}",
    summary="使用令牌验证账户",
    response={200: OutSchema[AccountOutSchema]},
)
def account_verify_confirm(
    request: HttpRequest,
    uidb64: str,
    token: str,
) -> Tuple[Literal[200], OutSchema[AccountOutSchema]]:
    """使用令牌验证账户"""

    try:
        # 解码 Base64 编码的用户 ID 并获取用户对象
        uid: str = force_str(urlsafe_base64_decode(uidb64))
        user: AbstractUser | None = User.objects.get(pk=uid)
        # 检查用户是否存在
        if user is None:
            raise Error(403, "account", "账户不存在")
        account: AbstractUser = AccountService.account_verify_confirm(user, token)
    except:
        raise Error(400, "token", "链接无效或已过期")
    return 200, OutSchema(data=AccountOutSchema.model_validate(account))


@router.get(
    "/accounts",
    summary="获取账户信息列表",
    response={200: OutSchema[List[AccountOutSchema]]},
)
def get_accounts(
    request: HttpRequest,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[Literal[200], OutSchema[List[AccountOutSchema]]]:
    """获取账户信息列表, 支持分页"""

    # 获取所有账户
    queryset: BaseManager[AbstractUser] = AccountService.get_accounts()
    # 分页
    start: int = (page - 1) * page_size
    end: int = start + page_size
    return 200, OutSchema(data=[AccountOutSchema.model_validate(account) for account in queryset[start:end]])


@router.patch(
    "/accounts/me",
    summary="更新当前账户信息",
    auth=OptionalAuth(),
    response={200: OutSchema[SensitiveAccountOutSchema], 400: OutSchema[None], 403: OutSchema[None]},
)
def update_my_account(
    request: HttpRequest,
    data: AccountUpdateInSchema,
) -> Tuple[Literal[200], OutSchema[SensitiveAccountOutSchema]]:
    """更新当前账户信息"""

    try:
        # 获取当前账户
        account: AbstractUser = AccountService.get_account(request.user.username)
        # 更新账户信息
        account: AbstractUser = AccountService.update_account(account, data)
    except:
        raise Error(404, "account", "未登录")
    return 200, OutSchema(data=SensitiveAccountOutSchema.model_validate(account))


@router.get(
    "/accounts/other/{username}",
    summary="获取账户信息",
    response={200: OutSchema[AccountOutSchema], 404: OutSchema[None]},
)
def get_account(
    request: HttpRequest,
    username: str,
) -> Tuple[Literal[200], OutSchema[AccountOutSchema]]:
    """获取特定账户信息, 不会输出敏感信息"""

    try:
        account: AbstractUser = AccountService.get_account(username)
    except:
        raise Error(404, "username", "用户不存在")
    return 200, OutSchema(data=AccountOutSchema.model_validate(account))


@router.get(
    "/accounts/me",
    summary="获取当前账户信息",
    auth=OptionalAuth(),
    response={200: OutSchema[SensitiveAccountOutSchema], 404: OutSchema[None]},
)
def get_my_account(
    request: HttpRequest,
) -> Tuple[Literal[200], OutSchema[SensitiveAccountOutSchema]]:
    """获取当前账户信息, 会输出敏感信息"""

    try:
        account: AbstractUser = AccountService.get_account(request.user.username)
    except:
        raise Error(404, "account", "未登录")
    return 200, OutSchema(data=SensitiveAccountOutSchema.model_validate(account))


@router.post(
    "/sessions",
    summary="登录账户",
    response={201: OutSchema[JwtOutSchema]},
)
def login(
    request: HttpRequest,
    data: LoginInSchema,
) -> Tuple[Literal[201], OutSchema[JwtOutSchema]]:
    """登录账户"""

    # 验证账户
    user: AbstractUser | None = authenticate(username=data.username, password=data.password)
    if user is None:
        raise Error(401, "password", "用户名或密码错误")
    else:
        if not user.is_active:
            raise Error(403, "account", "账户未激活, 请先验证邮箱")
        jwt: JwtOutSchema = AccountService.login(user)
    return 201, OutSchema(data=jwt)


@router.post(
    "/password-resets",
    summary="请求重置密码",
    response={201: OutSchema[str]},
)
def password_reset_request(
    request: HttpRequest,
    data: EmailRequestInSchema,
) -> Tuple[Literal[201], OutSchema[str]]:
    """请求重置密码"""

    try:
        user: AbstractUser | None = User.objects.get(email=data.email)
        AccountService.password_reset_request(user, data)
    except Exception as e:
        raise Error(500, "email", f"邮件发送失败: {str(e)}")
    return 201, OutSchema(data="如果邮箱存在, 重置链接已发送")


@router.put(
    "/password-resets/{uidb64}/{token}",
    summary="使用令牌重置密码",
    response={200: OutSchema[str]},
)
def password_reset_confirm(
    request: HttpRequest,
    uidb64: str,
    token: str,
    data: PasswordResetConfirmInSchema,
) -> Tuple[Literal[200], OutSchema[str]]:
    """使用令牌重置密码"""

    try:
        # 解码 Base64 编码的用户 ID 并获取用户对象
        uid: str = force_str(urlsafe_base64_decode(uidb64))
        user: AbstractUser = User.objects.get(pk=uid)
        # 检查用户是否已激活
        if not user.is_active:
            raise Error(403, "account", "账户未激活, 请先验证邮箱")
        result: str = AccountService.password_reset_confirm(user, token, data)
    except:
        raise Error(400, "token", "链接无效或已过期")
    return 200, OutSchema(data=result)
