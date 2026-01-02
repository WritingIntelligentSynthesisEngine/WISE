# book/endpoints.py
from typing import Optional, List, Tuple, Literal

from django.db.models import Q
from ninja.errors import HttpError
from django.http import HttpRequest
from ninja import Router, UploadedFile, File
from django.db.models.manager import BaseManager
from django.contrib.auth.models import AbstractUser, AnonymousUser

from core.schemas import OutSchema
from utils.exception_util import Error
from book.models import Category, Book, Chapter
from utils.authentication_util import OptionalAuth
from account.permissions import is_admin, is_active
from book.services import BookService, ChapterService
from book.permissions import can_delete, can_update, can_view
from book.schemas import (
    BookCreateInSchema,
    BookUpdateInSchema,
    BookOutSchema,
    ChapterCreateInSchema,
    ChapterUpdateInSchema,
    ChapterOutSchema,
)


router: Router = Router(tags=["书籍与文章"])


@router.post(
    "/books",
    summary="创建书籍",
    auth=OptionalAuth(),
    response={201: OutSchema[BookOutSchema]},
)
def create_book(
    request: HttpRequest,
    data: BookCreateInSchema,
) -> Tuple[Literal[201], OutSchema[BookOutSchema]]:
    """创建书籍, 如果有封面则保存在媒体目录, 并且创建用户与书籍的作者关系"""

    user: AbstractUser | AnonymousUser = request.user
    if not user.is_active:
        raise Error(403, "permission", "没有创建权限")
    try:
        category: Category | None = Category.objects.get(id=data.category_id) if data.category_id != None else None
    except Category.DoesNotExist:
        raise Error(404, "category_id", "无效的分类ID")
    book: Book = BookService.create_book(user, category, data)
    return 201, OutSchema(data=BookOutSchema.model_validate(book))


@router.delete(
    "/books/{book_id}",
    summary="删除书籍",
    auth=OptionalAuth(),
    response={204: OutSchema[None], 403: OutSchema[None], 404: OutSchema[None]},
)
def delete_book(
    request: HttpRequest,
    book_id: int,
) -> Tuple[Literal[204], OutSchema[None]]:
    """删除书籍接口, 要求用户必须是书籍的主创或管理员才能删除"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    if not can_delete(request.user, book):
        raise Error(403, "permission", "没有删除权限")
    BookService.delete_book(book)
    return 204, OutSchema(data=None)


@router.patch(
    "/books/{book_id}",
    summary="更新书籍",
    auth=OptionalAuth(),
    response={200: OutSchema[BookOutSchema], 403: OutSchema[None], 404: OutSchema[None]},
)
def update_book(
    request: HttpRequest,
    book_id: int,
    data: BookUpdateInSchema,
) -> Tuple[Literal[200], OutSchema[BookOutSchema]]:
    """更新书籍"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    if not can_update(request.user, book):
        raise HttpError(403, "没有更新权限")
    try:
        category: Category | None = Category.objects.get(id=data.category_id) if data.category_id != None else None
    except Category.DoesNotExist:
        raise Error(404, "category_id", "无效的分类ID")
    book = BookService.update_book(category, book, data)
    return 200, OutSchema(data=BookOutSchema.model_validate(book))


@router.patch(
    "/books/{book_id}/cover",
    summary="更新封面图片",
    auth=OptionalAuth(),
    response={200: OutSchema[BookOutSchema], 403: OutSchema[None], 404: OutSchema[None]},
)
def upload_cover_image(
    request: HttpRequest,
    book_id: int,
    cover_image: File[UploadedFile] = None,  # pyright: ignore[reportArgumentType]
) -> Tuple[Literal[200], OutSchema[BookOutSchema]]:
    """更新书籍封面"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 检查权限
    if not can_update(request.user, book):
        raise Error(403, "permission", "没有更新权限")
    if cover_image == None:
        # 删除封面
        BookService.delete_cover_image(book)
    else:
        # 更新封面
        book = BookService.update_cover_image(book, cover_image)
    return 200, OutSchema(data=BookOutSchema.model_validate(book))


@router.get(
    "/books",
    summary="获取书籍列表",
    auth=OptionalAuth(),
    response={200: OutSchema[List[BookOutSchema]]},
)
def get_books(
    request: HttpRequest,
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Tuple[Literal[200], OutSchema[List[BookOutSchema]]]:
    """获取书籍列表, 支持过滤和分页"""

    # 获取所有书籍
    queryset: BaseManager[Book] = BookService.get_books()
    # 获取用户
    user: AbstractUser | AnonymousUser = request.user
    # 过滤
    if not is_active(user):  # 未激活用户直接返回已发布的书籍
        queryset = queryset.filter(Q(status__in=["serializing", "completed"]))
    elif is_admin(user):  # 管理员直接返回全部书籍
        pass
    else:  # 认证用户返回已发布的书籍或自己管理的书籍
        queryset = queryset.filter(Q(status__in=["serializing", "completed"]) | (Q(status="draft") & Q(user_relations__user=user) & ~Q(user_relations__creative_role="reader"))).distinct()
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if status:
        queryset = queryset.filter(status=status)
    # 分页
    start: int = (page - 1) * page_size
    end: int = start + page_size
    return 200, OutSchema(data=[BookOutSchema.model_validate(book) for book in queryset[start:end]])


@router.get(
    "/books/{book_id}",
    summary="获取书籍",
    auth=OptionalAuth(),
    response={200: OutSchema[BookOutSchema], 403: OutSchema[None], 404: OutSchema[None]},
)
def get_book(
    request: HttpRequest,
    book_id: int,
) -> Tuple[Literal[200], OutSchema[BookOutSchema]]:
    """获取特定书籍"""

    # 获取书籍
    try:
        book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
        # 检查用户是否有权限查看书籍
    if not can_view(request.user, book):
        raise Error(403, "permission", "没有查看权限")
    return 200, OutSchema(data=BookOutSchema.model_validate(book))


@router.post(
    "/books/{book_id}/chapters",
    summary="创建章节",
    auth=OptionalAuth(),
    response={201: OutSchema[ChapterOutSchema], 403: OutSchema[None], 404: OutSchema[None]},
)
def create_chapter(
    request: HttpRequest,
    book_id: int,
    data: ChapterCreateInSchema,
) -> Tuple[Literal[201], OutSchema[ChapterOutSchema]]:
    """创建新章节"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 检查权限
    if not can_update(request.user, book):
        raise Error(403, "permission", "没有创建章节权限")
    # 创建章节
    chapter: Chapter = ChapterService.create_chapter(book, data)
    return 201, OutSchema(data=ChapterOutSchema.model_validate(chapter))


@router.patch(
    "/books/{book_id}/chapters/{chapter_number}",
    summary="更新章节",
    auth=OptionalAuth(),
    response={200: OutSchema[ChapterOutSchema], 403: OutSchema[None], 404: OutSchema[None]},
)
def update_chapter(
    request: HttpRequest,
    book_id: int,
    chapter_number: int,
    data: ChapterUpdateInSchema,
) -> Tuple[Literal[200], OutSchema[ChapterOutSchema]]:
    """更新章节信息"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 获取章节
    try:
        chapter: Chapter = ChapterService.get_chapter(book, chapter_number)
    except Chapter.DoesNotExist:
        raise Error(404, "chapter_number", "章节不存在")
    # 检查权限
    if not can_update(request.user, book):
        raise Error(403, "permission", "没有更新章节权限")
    # 更新章节
    chapter = ChapterService.update_chapter(chapter, data)
    return 200, OutSchema(data=ChapterOutSchema.model_validate(chapter))


@router.delete(
    "/books/{book_id}/chapters/{chapter_number}",
    summary="删除章节",
    auth=OptionalAuth(),
    response={204: OutSchema[None], 403: OutSchema[None], 404: OutSchema[None]},
)
def delete_chapter(
    request: HttpRequest,
    book_id: int,
    chapter_number: int,
) -> Tuple[Literal[204], OutSchema[None]]:
    """删除章节"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 获取章节
    try:
        chapter: Chapter = ChapterService.get_chapter(book, chapter_number)
    except Chapter.DoesNotExist:
        raise Error(404, "chapter_number", "章节不存在")
    # 检查权限
    if not can_delete(request.user, book):
        raise Error(403, "permission", "没有删除章节权限")
    # 删除章节
    ChapterService.delete_chapter(chapter)
    return 204, OutSchema(data=None)


@router.get(
    "/books/{book_id}/chapters",
    summary="获取章节列表",
    auth=OptionalAuth(),
    response={200: OutSchema[List[ChapterOutSchema]], 403: OutSchema[None], 404: OutSchema[None]},
)
def get_chapters(
    request: HttpRequest,
    book_id: int,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[Literal[200], OutSchema[List[ChapterOutSchema]]]:
    """获取书籍的章节列表"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 获取用户
    user: AbstractUser | AnonymousUser = request.user
    # 检查书籍权限
    if book.status == "draft" and not can_view(user, book):
        raise Error(403, "permission", "没有查看权限")
    # 获取所有章节
    queryset: BaseManager[Chapter] = ChapterService.get_chapters(book)
    # 分页
    start: int = (page - 1) * page_size
    end: int = start + page_size
    return 200, OutSchema(data=[ChapterOutSchema.model_validate(chapter) for chapter in queryset.order_by("chapter_number")[start:end]])


@router.get(
    "/books/{book_id}/chapters/{chapter_number}",
    summary="获取章节",
    auth=OptionalAuth(),
    response={200: OutSchema[ChapterOutSchema], 403: OutSchema[None], 404: OutSchema[None]},
)
def get_chapter(
    request: HttpRequest,
    book_id: int,
    chapter_number: int,
) -> Tuple[Literal[200], OutSchema[ChapterOutSchema]]:
    """获取特定章节"""

    # 获取书籍
    try:
        book: Book = BookService.get_book(book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 检查权限
    if not can_view(request.user, book):
        raise Error(403, "permission", "没有查看权限")
    # 获取章节
    try:
        chapter: Chapter = ChapterService.get_chapter(book, chapter_number)
    except Chapter.DoesNotExist:
        raise Error(404, "chapter_number", "章节不存在")
    return 200, OutSchema(data=ChapterOutSchema.model_validate(chapter))
