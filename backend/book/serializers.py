# book/serializers.py
from django.db.models import Q
from django_filters import FilterSet
from django.db.models.manager import BaseManager
from django.contrib.auth.models import AbstractUser, AnonymousUser

from book.models import Book
from core.permissions import is_admin

class BookFilter(FilterSet):
    @staticmethod
    def view_permission_filter(books: BaseManager[Book], user: AbstractUser|AnonymousUser) -> BaseManager[Book]:
        """过滤出用户有权限查阅的书籍

        参数:
            books (BaseManager[Book]): _description_
            user (AbstractUser | AnonymousUser): _description_

        返回:
            对于管理员, 返回所有的书籍
            对于匿名用户, 只返回已发布的书籍
            对于认证用户, 返回返回已发布的书籍或自己管理的书籍
        """
        # 管理员直接返回全部书籍
        if is_admin(user):
            return books
        # 匿名用户直接返回已发布的书籍
        if user.is_anonymous:
            return books.filter(Q(status__in=['serializing', 'completed']))
        # 认证用户返回已发布的书籍或自己管理的书籍
        return books.filter(
            Q(status__in=['serializing', 'completed']) |
            (
                Q(status='draft') &
                Q(user_relations__user=user) &
                ~Q(user_relations__creative_role='reader')
            )
        ).distinct()
