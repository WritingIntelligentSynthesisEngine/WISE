# book/permissions.py
from django.contrib.auth.models import AbstractUser, AnonymousUser

from book.models import Book, UserBookRelation
from account.permissions import is_admin, is_active


def is_author(user: AbstractUser | AnonymousUser, book: Book) -> bool:
    """是否为主创"""

    return UserBookRelation.objects.filter(
        book=book,
        user=user,
        creative_role__in=["author"],
    ).exists()


def is_co_author(user: AbstractUser | AnonymousUser, book: Book) -> bool:
    """是否为共创"""

    return UserBookRelation.objects.filter(
        book=book,
        user=user,
        creative_role__in=["co_author"],
    ).exists()


def is_editor(user: AbstractUser | AnonymousUser, book: Book) -> bool:
    """是否为编辑"""

    return UserBookRelation.objects.filter(
        book=book,
        user=user,
        creative_role__in=["editor"],
    ).exists()


def can_delete(user: AbstractUser | AnonymousUser, book: Book) -> bool:
    """管理员和主创有删除权限"""

    return is_admin(user) or is_author(user, book)


def can_update(user: AbstractUser | AnonymousUser, book: Book) -> bool:
    """管理员、主创和共创有更新权限"""

    return is_admin(user) or is_author(user, book) or is_co_author(user, book)


def can_view(user: AbstractUser | AnonymousUser, book: Book) -> bool:
    """未发布时, 未激活用户和读者没有查阅权限"""

    if book.status != "draft":
        return True
    if is_active(user):
        return False
    return is_admin(user) or is_author(user, book) or is_co_author(user, book) or is_editor(user, book)
