# book/routers.py
import os
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, UploadedFile, File

from utils import path_util
from book.models import Book, Category

router = Router(tags=["书籍与文章"])


class BookIn(Schema):
    category_id: int = 1
    title: str
    description: str = "无"
    status: str = "draft"
    attributes: Dict[str, Any] = {}


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
    response=BookOut,
    summary="创建新书籍",
)
def create_book(
    request: Any,
    data: BookIn,
    cover_image: UploadedFile = File(None), # type: ignore
) -> Book:
    """创建新书籍, 如果有封面则保存在媒体目录, 并且创建用户与书籍的作者关系"""
    # 获取分类
    category: Category = get_object_or_404(Category, id=data.category_id)
    # 处理封面图片
    cover_image_path: Path = Path()
    if cover_image:
        # 生成基于哈希的路径
        cover_image_path: Path = path_util.generate_hash_path(cover_image)
        # 完整路径
        full_path: Path = settings.MEDIA_ROOT / Path("covers") / cover_image_path
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # 只有在文件不存在时才保存
        if not os.path.exists(full_path):
            with open(full_path, 'wb+') as destination:
                for chunk in cover_image.chunks():
                    destination.write(chunk)
    # 创建书籍
    book: Book = Book.objects.create(
        category=category,
        title=data.title,
        description=data.description,
        cover_image_path=str(cover_image_path),
        status=data.status,
        attributes=data.attributes,
    )
    return book
