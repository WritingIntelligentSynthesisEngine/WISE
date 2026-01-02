# account/schemas.py
from datetime import datetime
from decimal import Decimal
from typing import Type, Self, Optional
from pydantic import ValidationInfo, EmailStr, field_validator

from ninja import Schema

from utils.exception_util import Error


class UsernameValidatorMixin:
    """用户名验证混合类，提供通用的用户名验证方法"""

    @field_validator("username")
    @classmethod
    def username_length(cls: Type[Self], v: str) -> str:
        if len(v) < 3:
            raise Error(400, "username", "用户名至少需要3个字符")
        return v


class PasswordValidatorMixin:
    """密码验证混合类，提供通用的密码验证方法"""

    @field_validator("password")
    @classmethod
    def password_strength(cls: Type[Self], v: str) -> str:
        if len(v) < 8:
            raise Error(400, "password", "密码至少需要8个字符")
        # TODO: 添加更多密码强度检查
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls: Type[Self], v: str, info: ValidationInfo) -> str:
        password_field = "password"
        if password_field in info.data and v != info.data[password_field]:
            raise Error(400, "password", "密码不匹配")
        return v


class RegisterInSchema(Schema, UsernameValidatorMixin, PasswordValidatorMixin):
    """注册账户时输入"""

    username: str
    email: EmailStr
    password: str
    password_confirm: str


class AccountUpdateInSchema(Schema, UsernameValidatorMixin):
    """更新账户信息时输入"""

    username: Optional[str] = None
    api_key: Optional[str] = None


class AccountOutSchema(Schema):
    """账户信息输出"""

    last_login: Optional[datetime]
    is_superuser: bool
    username: str
    email: str
    is_staff: bool
    is_active: bool
    date_joined: datetime
    profile_image_path: str


class SensitiveAccountOutSchema(AccountOutSchema):
    """敏感账户信息输出"""

    balance: Decimal
    api_key: str


class LoginInSchema(Schema):
    """登录账户时输入"""

    username: str
    password: str


class JwtOutSchema(Schema):
    """JWT 输出"""

    access: str
    refresh: str


class EmailRequestInSchema(Schema):
    """邮箱验证时输入"""

    email: EmailStr


class PasswordResetConfirmInSchema(Schema, PasswordValidatorMixin):
    """确认重置密码时输入"""

    password: str
    password_confirm: str
