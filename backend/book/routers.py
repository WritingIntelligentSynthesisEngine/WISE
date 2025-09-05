# book/routers.py
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List, Dict, Tuple, Literal

from django.conf import settings
from ninja.errors import HttpError
from django.http import HttpRequest
from ninja_jwt.authentication import JWTAuth
from django.db.models.manager import BaseManager
from ninja import Router, Schema, UploadedFile, File

from utils import path_util
from book.serializers import BookFilter
from utils.authentication_util import OptionalAuth
from book.models import Book, Category, UserBookRelation
from book.permissions import can_delete_book, can_update_book, can_view_book


router = Router(tags=["书籍与文章"])


class BookCreateIn(Schema):
    category_id: int = 1
    title: str
    description: str = "无"
    attributes: Dict[str, Any] = {}


class BookUpdateIn(Schema):
    category_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class BookOut(Schema):
    id: int
    category_id: int
    title: str
    description: str
    cover_image_path: str
    create_time: datetime
    update_time: datetime
    status: str
    attributes: Dict[str, Any]


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
        category: Category = Category.objects.get(id=data.category_id)
    except Category.DoesNotExist:
        raise HttpError(404, "分类不存在")
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
    if not can_delete_book(request.user, book):
        raise HttpError(403, "没有删除权限")
    # 只删除数据库记录, 这会级联删除所有相关的关系记录, 但不删除封面文件
    book.delete()
    return 204, None


@router.patch(
    "/books/{book_id}/",
    summary="更新书籍信息",
    auth=JWTAuth(),
    response={200: BookOut, 403: Dict[str, str], 404: Dict[str, str]},
)
def update_book(
    request: HttpRequest,
    book_id: int,
    data: BookUpdateIn,
    cover_image: Optional[UploadedFile] = File(None),  # type: ignore
) -> Tuple[Literal[200], Book]:
    """更新书籍信息"""
    # 获取要更新的书籍
    try:
        book: Book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
    # 检查权限
    if not can_update_book(request.user, book):
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
    auth=OptionalAuth(),
    response={200: List[BookOut], 400: Dict[str, str]},
)
def get_books(
    request: HttpRequest,
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
) -> BaseManager[Book]:
    """获取书籍列表, 支持过滤和分页"""
    # 获取所有书籍
    queryset: BaseManager[Book] = Book.objects.all()
    # 过滤
    queryset = BookFilter.view_permission_filter(Book.objects.all(), request.user)
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if status:
        queryset = queryset.filter(status=status)
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    return queryset[start:end]


@router.get(
    "/books/{book_id}/",
    summary="获取书籍详情",
    auth=OptionalAuth(),
    response={200: BookOut, 403: Dict[str, str], 404: Dict[str, str]},
)
def get_book(
    request: HttpRequest,
    book_id: int,
) -> Book:
    """获取特定书籍的详细信息"""
    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        raise HttpError(404, "书籍不存在")
        # 检查用户是否有权限查看书籍
    if book.status == "draft" and not can_view_book(request.user, book):
        raise HttpError(403, "没有查看权限")
    return book


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
