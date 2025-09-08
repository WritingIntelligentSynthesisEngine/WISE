# core/permissions.py
from django.contrib.auth.models import AbstractUser, AnonymousUser


def is_admin(user: AbstractUser | AnonymousUser) -> bool:
    """是否为管理员"""
    return user.is_staff or user.is_superuser


def is_active(user: AbstractUser | AnonymousUser) -> bool:
    """是否为激活用户"""
    return user.is_active


def is_anonymous(user: AbstractUser | AnonymousUser) -> bool:
    """是否为匿名用户"""
    return user.is_anonymous
