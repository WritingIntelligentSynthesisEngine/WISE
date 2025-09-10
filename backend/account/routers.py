# account/routers.py
from typing import Self, Dict, Tuple, Literal

from ninja import Router
from django.conf import settings
from ninja.errors import HttpError
from django.http import HttpRequest
from ninja_jwt.tokens import RefreshToken
from django.core.mail import EmailMessage
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.auth.models import AbstractUser
from django.utils.encoding import force_str, force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from account.schemas import RegisterIn, AccountOut, LoginIn, LoginOut


User = get_user_model()

router = Router(tags=["账户"])


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self: Self, user, timestamp) -> str:
        return f"{user.pk}{timestamp}{user.is_active}"


account_activation_token: AccountActivationTokenGenerator = AccountActivationTokenGenerator()


@router.post(
    "/register",
    summary="注册账户",
    response={201: AccountOut, 400: Dict[str, str]},
)
def register(request: HttpRequest, data: RegisterIn) -> Tuple[Literal[201], AccountOut]:
    """注册账户并发送验证邮件"""
    # 验证用户名或邮箱是否被占用
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "用户名已存在")
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "邮箱已被注册")
    # 创建未激活用户
    user: AbstractUser = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        is_active=False,
    )
    # 邮件主题
    mail_subject: str = "激活您的账户"
    # 邮件消息
    message: str = render_to_string(
        "active_email.html",
        {
            "user": user,
            "frontend_domain": settings.FRONTEND_DOMAIN,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        },
    )
    # 创建邮件
    email: EmailMessage = EmailMessage(mail_subject, message, to=[data.email])
    # 设置为 HTML 内容类型
    email.content_subtype = "html"
    # 发送邮件
    email.send()
    return 201, AccountOut(
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        date_joined=user.date_joined,
    )


@router.get(
    "/verify/{uidb64}/{token}",
    summary="验证账户",
    response={200: AccountOut, 400: Dict[str, str]},
)
def verify(request: HttpRequest, uidb64: str, token: str) -> Tuple[Literal[200], AccountOut]:
    """验证账户"""
    try:
        uid: str = force_str(urlsafe_base64_decode(uidb64))
        user: AbstractUser | None = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return 200, AccountOut(
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            date_joined=user.date_joined,
        )
    else:
        raise HttpError(400, "验证链接无效")


@router.post(
    "/login",
    summary="登录账户",
    response={201: LoginOut, 401: Dict[str, str], 403: Dict[str, str]},
)
def login(request: HttpRequest, data: LoginIn) -> Tuple[Literal[201], LoginOut]:
    """登录账户"""
    # 验证账户
    user: AbstractUser | None = authenticate(username=data.username, password=data.password)
    if user is None:
        raise HttpError(401, "用户名或密码错误")
    if not user.is_active:
        raise HttpError(403, "账户未激活, 请先验证邮箱")
    # 生成 JWT 令牌
    refresh: RefreshToken = RefreshToken.for_user(user)  # type: ignore
    return 201, LoginOut(
        access=str(refresh.access_token),
        refresh=str(refresh),
        account=AccountOut(
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            date_joined=user.date_joined,
        ),
    )
