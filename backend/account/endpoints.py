# account/endpoints.py
from typing import Self, Dict, Tuple, Literal

from ninja import Router
from django.conf import settings
from django.db import transaction
from ninja.errors import HttpError
from django.http import HttpRequest
from ninja_jwt.tokens import RefreshToken
from django.core.mail import EmailMessage
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.auth.models import AbstractUser
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from account.schemas import RegisterIn, AccountOut, LoginIn, LoginOut, PasswordResetRequestIn, PasswordResetConfirmIn


router: Router = Router(tags=["账户"])


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """用于生成账户激活令牌的类

    通过重写 _make_hash_value 方法, 使用用户的主键、时间戳和激活状态来生成令牌的哈希值,这样可以确保令牌与用户的当前是否激活相关联, 提高安全性
    """

    def _make_hash_value(self: Self, user, timestamp) -> str:
        return f"{user.pk}{timestamp}{user.is_active}"


# 动态获取当前项目中配置的用户模型类
User: type[AbstractUser] = get_user_model()

account_activation_token: AccountActivationTokenGenerator = AccountActivationTokenGenerator()
password_reset_token: PasswordResetTokenGenerator = PasswordResetTokenGenerator()


@router.post(
    "/register",
    summary="注册账户",
    response={201: AccountOut, 400: Dict[str, str], 500: Dict[str, str]},
)
@transaction.atomic
def register(request: HttpRequest, data: RegisterIn) -> Tuple[Literal[201], AccountOut]:
    """注册账户并发送验证邮件, 如果邮箱已被注册但未激活, 则更新用户信息并重新发送激活邮件"""
    # 检查用户名是否已被占用
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "用户名已存在")
    # 检查邮箱是否已被注册
    if existing_user := User.objects.filter(email=data.email).first():
        # 如果邮箱已注册且已激活, 返回错误
        if existing_user.is_active:
            raise HttpError(400, "邮箱已被注册")
        # 如果邮箱已注册但未激活, 更新用户信息并重新发送激活邮件
        existing_user.username = data.username
        existing_user.set_password(data.password)
        existing_user.save()
        user: AbstractUser = existing_user
    else:
        # 创建新用户
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
        "html/active_email.html",
        {
            "user": user,
            "frontend_domain": settings.CSRF_TRUSTED_ORIGINS[0],
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        },
    )
    # 创建邮件
    email: EmailMessage = EmailMessage(mail_subject, message, to=[data.email])
    # 设置为 HTML 内容类型
    email.content_subtype = "html"
    # 发送邮件
    try:
        email.send()
        return 201, AccountOut(
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            date_joined=user.date_joined,
        )
    except Exception as e:
        # 如果发送邮件失败, 事务会自动回滚, 用户不会被创建或更新
        raise HttpError(500, f"邮件发送失败: {str(e)}")


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
        raise HttpError(400, "验证链接无效或已过期")


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


@router.post(
    "/password-reset-request",
    summary="请求重置密码",
    response={200: Dict[str, str], 500: Dict[str, str]},
)
def password_reset_request(request: HttpRequest, data: PasswordResetRequestIn) -> Tuple[Literal[200], Dict[str, str]]:
    """请求重置密码"""
    try:
        user: AbstractUser | None = User.objects.get(email=data.email)
    except User.DoesNotExist:
        # 出于安全考虑, 即使邮箱不存在也返回成功
        return 200, {"message": "如果邮箱存在, 重置链接已发送"}
    # 邮件主题
    mail_subject: str = "重置您的密码"
    # 邮件消息
    message: str = render_to_string(
        "html/password_reset_email.html",
        {
            "user": user,
            "frontend_domain": settings.CSRF_TRUSTED_ORIGINS[0],
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": password_reset_token.make_token(user),
        },
    )
    # 创建邮件
    email: EmailMessage = EmailMessage(mail_subject, message, to=[data.email])
    # 设置为 HTML 内容类型
    email.content_subtype = "html"
    # 发送邮件
    try:
        email.send()
        return 200, {"message": "如果邮箱存在, 重置链接已发送"}
    except Exception as e:
        raise HttpError(500, f"邮件发送失败: {str(e)}")


@router.post(
    "/password-reset-confirm/{uidb64}/{token}",
    summary="确认重置密码",
    response={200: Dict[str, str], 400: Dict[str, str], 403: Dict[str, str]},
)
def password_reset_confirm(request: HttpRequest, uidb64: str, token: str, data: PasswordResetConfirmIn) -> Tuple[Literal[200], Dict[str, str]]:
    """确认重置密码"""
    try:
        # 解码 Base64 编码的用户 ID 并获取用户对象
        uid: str = force_str(urlsafe_base64_decode(uidb64))
        user: AbstractUser | None = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise HttpError(400, "重置链接无效或已过期")
    # 验证令牌有效性
    if user is not None and password_reset_token.check_token(user, token):
        # 检查用户是否已激活
        if not user.is_active:
            raise HttpError(403, "账户未激活, 请先验证邮箱")
        # 设置新密码并保存用户
        user.set_password(data.password)
        user.save()
        return 200, {"message": "密码重置成功"}
    else:
        raise HttpError(400, "重置链接无效或已过期")
