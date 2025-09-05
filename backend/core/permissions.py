# core/permissions.py
from django.contrib.auth.models import AbstractUser, AnonymousUser


def is_admin(user: AbstractUser | AnonymousUser) -> bool:
    """是否为管理员"""
    return user.is_staff or user.is_superuser
