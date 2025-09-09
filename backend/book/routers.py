# book/routers.py
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Literal

from django.db.models import Q
from django.conf import settings
from ninja.errors import HttpError
from django.http import HttpRequest
from ninja import Router, UploadedFile, File
from ninja_jwt.authentication import JWTAuth
from django.db.models.manager import BaseManager
from django.contrib.auth.models import AbstractUser, AnonymousUser

from utils import path_util, authentication_util
from core.permissions import is_admin, is_active
from book.permissions import can_delete, can_update, can_view
from book.models import Book, Category, UserBookRelation, Chapter
from book.schemas import BookCreateIn, BookUpdateIn, BookOut, ChapterCreateIn, ChapterUpdateIn, ChapterOut


router = Router(tags=["书籍与文章"])


@router.post(
    "/books/",
    summary="创建书籍",
    auth=JWTAuth(),
    response={201: BookOut, 404: Dict[str, str]},
)
def create_book(
    request: HttpRequest,
    data: BookCreateIn,
    cover_image: Optional[UploadedFile] = File(None),  # type: ignore
) -> Tuple[Literal[201], Book]:
    """创建书籍, 如果有封面则保存在媒体目录, 并且创建用户与书籍的作者关系"""
    # 获取分类
    try:
        category: Category | None = Category.objects.get(id=data.category_id)
    except Category.DoesNotExist:
        category = None
    # 创建书籍
    book: Book = Book.objects.create(
        category=category,
        title=data.title,
        description=data.description,
        cover_image_path=save_cover_image(cover_image),
        status="draft",
        attributes=data.attributes,
    )
    # 创建用户与书籍的作者关系
    UserBookRelation.objects.create(
        book=book,
        user=request.user,
        creative_role="author",
    )
    return 201, book


@router.delete(
    "/books/{book_id}/",
    summary="删除书籍",
    auth=JWTAuth(),
    response={204: None, 403: Dict[str, str], 404: Dict[str, str]},
)
def delete_book(
    request: HttpRequest,
    book_id: int,
) -> Tuple[Literal[204], None]:
    """删除书籍接口, 要求用户必须是书籍的主创或管理员才能删除"""
    # 获取要删除的书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 检查权限
    if not can_delete(request.user, book):
        raise HttpError(403, "没有删除权限")
    # 只删除数据库记录, 这会级联删除所有相关的关系记录, 但不删除封面文件
    book.delete()
    return 204, None


@router.patch(
    "/books/{book_id}/",
    summary="更新书籍",
    auth=JWTAuth(),
    response={200: BookOut, 403: Dict[str, str], 404: Dict[str, str]},
)
def update_book(
    request: HttpRequest,
    book_id: int,
    data: BookUpdateIn,
    cover_image: Optional[UploadedFile] = File(None),  # type: ignore
) -> Tuple[Literal[200], Book]:
    """更新书籍"""
    # 获取要更新的书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 检查权限
    if not can_update(request.user, book):
        raise HttpError(403, "没有更新权限")
    # 只更新提供的字段
    if data.title is not None:
        book.title = data.title
    if data.description is not None:
        book.description = data.description
    if data.attributes is not None:
        book.attributes = data.attributes
    if data.category_id is not None:
        try:
            category: Category = Category.objects.get(id=data.category_id)
            book.category = category
        except Category.DoesNotExist:
            raise HttpError(404, "无效的分类ID")
    if cover_image is not None:
        book.cover_image_path = save_cover_image(cover_image)
    book.save()
    return 200, book


# 获取书籍列表
@router.get(
    "/books/",
    summary="获取书籍列表",
    auth=authentication_util.OptionalAuth(),
    response={200: List[BookOut]},
)
def get_books(
    request: HttpRequest,
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
) -> Tuple[Literal[200], BaseManager[Book]]:
    """获取书籍列表, 支持过滤和分页"""
    # 获取所有书籍
    queryset: BaseManager[Book] = Book.objects.all()
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
    return 200, queryset[start:end]


@router.get(
    "/books/{book_id}/",
    summary="获取书籍",
    auth=authentication_util.OptionalAuth(),
    response={200: BookOut, 403: Dict[str, str], 404: Dict[str, str]},
)
def get_book(
    request: HttpRequest,
    book_id: int,
) -> Tuple[Literal[200], Book]:
    """获取特定书籍"""
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
        # 检查用户是否有权限查看书籍
    if book.status == "draft" and not can_view(request.user, book):
        raise HttpError(403, "没有查看权限")
    return 200, book


@router.post(
    "/books/{book_id}/chapters/",
    summary="创建章节",
    auth=JWTAuth(),
    response={201: ChapterOut, 400: Dict[str, str], 403: Dict[str, str], 404: Dict[str, str]},
)
def create_chapter(
    request: HttpRequest,
    book_id: int,
    data: ChapterCreateIn,
) -> Tuple[Literal[201], Chapter]:
    """创建新章节"""
    # 获取书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 检查权限
    if not can_update(request.user, book):
        raise HttpError(403, "没有创建章节权限")
    # 检查章数是否已存在
    if Chapter.objects.filter(book=book, chapter_number=data.chapter_number).exists():
        raise HttpError(400, "该章数已存在")
    # 创建章节
    chapter: Chapter = Chapter.objects.create(
        book=book,
        chapter_number=data.chapter_number,
        title=data.title,
        content=data.content,
    )
    return 201, chapter


@router.patch(
    "/books/{book_id}/chapters/{chapter_number}/",
    summary="更新章节",
    auth=JWTAuth(),
    response={200: ChapterOut, 400: Dict[str, str], 403: Dict[str, str], 404: Dict[str, str]},
)
def update_chapter(
    request: HttpRequest,
    book_id: int,
    chapter_number: int,
    data: ChapterUpdateIn,
) -> Tuple[Literal[200], Chapter]:
    """更新章节信息"""
    # 获取书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 获取章节
    try:
        chapter: Chapter = Chapter.objects.get(book_id=book_id, chapter_number=chapter_number)
    except Chapter.DoesNotExist:
        raise HttpError(404, "章节不存在")
    # 检查权限
    if not can_update(request.user, book):
        raise HttpError(403, "没有更新章节权限")
    # 更新字段
    if data.chapter_number is not None:
        # 检查新章数是否已存在(排除自身)
        if Chapter.objects.filter(book_id=book_id, chapter_number=data.chapter_number).exclude(id=chapter.id).exists():
            raise HttpError(400, "该章数已存在")
        chapter.chapter_number = data.chapter_number
    if data.title is not None:
        chapter.title = data.title
    if data.content is not None:
        chapter.content = data.content
    if data.status is not None:
        chapter.status = data.status
    chapter.save()
    return 200, chapter


@router.delete(
    "/books/{book_id}/chapters/{chapter_number}/",
    summary="删除章节",
    auth=JWTAuth(),
    response={204: None, 403: Dict[str, str], 404: Dict[str, str]},
)
def delete_chapter(
    request: HttpRequest,
    book_id: int,
    chapter_number: int,
) -> Tuple[Literal[204], None]:
    """删除章节"""
    # 获取书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 获取章节
    try:
        chapter: Chapter = Chapter.objects.get(book_id=book_id, chapter_number=chapter_number)
    except Chapter.DoesNotExist:
        raise HttpError(404, "章节不存在")
    # 检查权限
    if not can_delete(request.user, book):
        raise HttpError(403, "没有删除章节权限")
    # 删除章节
    chapter.delete()
    return 204, None


@router.get(
    "/books/{book_id}/chapters/",
    summary="获取章节列表",
    auth=authentication_util.OptionalAuth(),
    response={200: List[ChapterOut], 403: Dict[str, str], 404: Dict[str, str]},
)
def get_chapters(
    request: HttpRequest,
    book_id: int,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[Literal[200], BaseManager[Chapter]]:
    """获取书籍的章节列表"""
    # 获取书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 获取用户
    user: AbstractUser | AnonymousUser = request.user
    # 检查书籍权限
    if book.status == "draft" and not can_view(user, book):
        raise HttpError(403, "没有查看权限")
    # 获取所有章节
    queryset: BaseManager[Chapter] = Chapter.objects.filter(book=book)
    # 如果没有查阅权限, 只返回已发布的章节
    if not can_view(user, book):
        queryset = queryset.filter(status="published")
    # 分页
    start: int = (page - 1) * page_size
    end: int = start + page_size
    return 200, queryset.order_by("chapter_number")[start:end]


@router.get(
    "/books/{book_id}/chapters/{chapter_number}/",
    summary="获取章节",
    auth=authentication_util.OptionalAuth(),
    response={200: ChapterOut, 403: Dict[str, str], 404: Dict[str, str]},
)
def get_chapter(
    request: HttpRequest,
    book_id: int,
    chapter_number: int,
) -> Tuple[Literal[200], Chapter]:
    """获取特定章节"""
    # 获取书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 获取章节
    try:
        chapter: Chapter = Chapter.objects.get(book_id=book_id, chapter_number=chapter_number)
    except Chapter.DoesNotExist:
        raise HttpError(404, "章节不存在")
    # 检查权限
    if not can_view(request.user, book):
        raise HttpError(403, "没有查看权限")
    return 200, chapter


def save_cover_image(cover_image: Optional[UploadedFile]) -> str:
    """保存封面图片"""
    # 如果没有文件则直接返回空字符串
    if cover_image is None:
        return ""
    # 生成基于哈希的路径
    cover_image_path: Path = path_util.generate_hash_path(cover_image)
    # 完整路径
    full_path: Path = settings.MEDIA_ROOT / Path("covers") / cover_image_path
    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    # 只有在文件不存在时才保存
    if not os.path.exists(full_path):
        with open(full_path, "wb+") as destination:
            for chunk in cover_image.chunks():
                destination.write(chunk)
    return str(cover_image_path)
