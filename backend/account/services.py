# account/services.py
from typing import Self, cast

from django.conf import settings
from django.db import transaction
from django.core.mail import EmailMessage
from ninja_jwt.tokens import RefreshToken
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.db.models.manager import BaseManager
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from account.schemas import (
    RegisterInSchema,
    EmailRequestInSchema,
    JwtOutSchema,
    PasswordResetConfirmInSchema,
)


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


class AccountService:
    """账户服务类"""

    @staticmethod
    @transaction.atomic
    def register(
        user: AbstractUser | None,
        data: RegisterInSchema,
    ) -> AbstractUser:
        """注册账户, 如果用户已存在但未激活, 则更新用户信息"""

        if user is None:
            # 如果用户不存在则创建新用户
            user = User.objects.create_user(
                username=data.username,
                email=data.email,
                password=data.password,
                is_active=False,
            )
        else:
            # 如果用户已存在但未激活则更新用户信息
            user.username = data.username
            user.set_password(data.password)
            user.save()
        return user

    @staticmethod
    def account_verify_request(
        user: AbstractUser,
        data: EmailRequestInSchema,
    ) -> None:
        """请求验证账户"""

        # 如果邮箱已注册但未激活, 更新用户信息并重新发送激活邮件
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
        email.send()

    @staticmethod
    def account_verify_confirm(
        user: AbstractUser,
        token: str,
    ) -> AbstractUser:
        """验证账户"""

        # 验证令牌有效性
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            return user
        else:
            raise

    @staticmethod
    def get_account(
        username: str,
    ) -> AbstractUser:
        """获取账户信息"""

        return User.objects.get(username=username)

    @staticmethod
    def get_accounts() -> BaseManager[AbstractUser]:
        """获取所有账户"""

        return User.objects.all()

    @staticmethod
    def login(
        user: AbstractUser,
    ) -> JwtOutSchema:
        """登录账户"""

        # 生成 JWT 令牌
        refresh: RefreshToken = cast(RefreshToken, RefreshToken.for_user(user))
        return JwtOutSchema(
            access=str(refresh.access_token),
            refresh=str(refresh),
        )

    @staticmethod
    def password_reset_request(
        user: AbstractUser,
        data: EmailRequestInSchema,
    ) -> None:
        """请求重置密码"""

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
        email.send()

    @staticmethod
    @transaction.atomic
    def password_reset_confirm(
        user: AbstractUser,
        token: str,
        data: PasswordResetConfirmInSchema,
    ) -> str:
        """确认重置密码"""

        # 验证令牌有效性
        if password_reset_token.check_token(user, token):
            # 设置新密码并保存用户
            user.set_password(data.password)
            user.save()
            return "密码重置成功"
        else:
            raise
