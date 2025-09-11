# account/schemas.py
from datetime import datetime
from typing import Type, Self
from pydantic import ValidationInfo, EmailStr, field_validator

from ninja import Schema


class UsernameValidatorMixin:
    """用户名验证混合类，提供通用的用户名验证方法"""

    @field_validator("username")
    @classmethod
    def username_length(cls: Type[Self], v: str) -> str:
        if len(v) < 3:
            raise ValueError("用户名至少需要3个字符")
        return v


class PasswordValidatorMixin:
    """密码验证混合类，提供通用的密码验证方法"""

    @field_validator("password")
    @classmethod
    def password_strength(cls: Type[Self], v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码至少需要8个字符")
        # TODO: 添加更多密码强度检查
        return v

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls: Type[Self], v: str, info: ValidationInfo) -> str:
        password_field = "password"
        if password_field in info.data and v != info.data[password_field]:
            raise ValueError("密码不匹配")
        return v


class RegisterIn(Schema, UsernameValidatorMixin, PasswordValidatorMixin):
    """注册账户时输入"""

    username: str
    email: EmailStr
    password: str
    password_confirm: str


class AccountOut(Schema):
    """账户信息输出"""

    username: str
    email: str
    is_active: bool
    date_joined: datetime


class LoginIn(Schema):
    """登录账户时输入"""

    username: str
    password: str


class LoginOut(Schema):
    """登录账户时输出"""

    access: str
    refresh: str
    account: AccountOut


class PasswordResetRequestIn(Schema):
    """请求重置密码时输入"""

    email: EmailStr


class PasswordResetConfirmIn(Schema, PasswordValidatorMixin):
    """确认重置密码时输入"""

    password: str
    password_confirm: str
