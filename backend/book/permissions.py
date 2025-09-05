# book/permissions.py
from django.contrib.auth.models import AbstractUser, AnonymousUser

from core.permissions import is_admin
from book.models import Book, UserBookRelation


def is_author(user: AbstractUser|AnonymousUser, book: Book) -> bool:
    """是否为主创"""
    return UserBookRelation.objects.filter(
        book=book,
        user=user,
        creative_role__in=['author']
    ).exists()


def is_co_author(user: AbstractUser|AnonymousUser, book: Book) -> bool:
    """是否为共创"""
    return UserBookRelation.objects.filter(
        book=book,
        user=user,
        creative_role__in=['co_author']
    ).exists()


def is_editor(user: AbstractUser|AnonymousUser, book: Book) -> bool:
    """是否为编辑"""
    return UserBookRelation.objects.filter(
        book=book,
        user=user,
        creative_role__in=['editor']
    ).exists()


def can_delete_book(user: AbstractUser|AnonymousUser, book: Book) -> bool:
    """管理员和主创有删除权限"""
    return is_admin(user) or is_author(user, book)


def can_update_book(user: AbstractUser|AnonymousUser, book: Book) -> bool:
    """管理员、主创和共创有更新权限"""
    return is_admin(user) or is_author(user, book) or is_co_author(user, book)


def can_view_book(user: AbstractUser|AnonymousUser, book: Book) -> bool:
    """未发布时, 非普通读者有查阅权限"""
    return is_admin(user) or is_author(user, book) or is_co_author(user, book) or is_editor(user, book)

