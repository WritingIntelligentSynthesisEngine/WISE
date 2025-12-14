# book/services.py
import os
from pathlib import Path
from typing import Optional, List, Dict

from django.conf import settings
from django.db import transaction
from utils.exception_util import Error
from ninja import UploadedFile, File
from django.db.models.manager import BaseManager
from django.contrib.auth.models import AbstractUser, AnonymousUser

from utils import path_util
from book.models import Category, Book, UserBookRelation, Chapter
from book.schemas import BookCreateInSchema, BookUpdateInSchema, ChapterCreateInSchema, ChapterUpdateInSchema


class BookService:
    """书籍服务类"""

    @staticmethod
    @transaction.atomic
    def create_book(
        data: BookCreateInSchema,
        user: AbstractUser | AnonymousUser,
        category: Category,
        cover_image: File[UploadedFile],
    ) -> Book:
        """创建书籍, 并且创建用户与书籍的作者关系, 如果有封面则保存在媒体目录"""

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
            user=user,
            creative_role="author",
        )
        return book

    @staticmethod
    @transaction.atomic
    def delete_book(
        book: Book,
    ) -> None:
        """删除书籍"""

        # 获取封面图片路径
        cover_image_path: str = book.cover_image_path
        # 先删除数据库记录, 这会级联删除所有相关的关系记录
        book.delete()
        # 检索引用计数, 如果为 0 则删除封面图片
        if cover_image_path:
            # 检查是否有其他书籍使用相同的封面图片路径
            other_books_with_same_cover: bool = Book.objects.filter(cover_image_path=cover_image_path).exists()
            # 如果没有其他书籍使用相同的封面图片, 则删除文件
            if not other_books_with_same_cover:
                try:
                    full_path: Path = settings.MEDIA_ROOT / Path("covers") / Path(cover_image_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        # 尝试删除可能的空目录
                        try:
                            os.removedirs(os.path.dirname(full_path))
                        except OSError:
                            # 目录不为空或无法删除, 忽略错误
                            pass
                except (OSError, FileNotFoundError):
                    # 文件删除失败, 记录日志或忽略
                    pass
        return None

    @staticmethod
    @transaction.atomic
    def update_book(
        book: Book,
        data: BookUpdateInSchema,
        cover_image: File[UploadedFile],
    ) -> Book:
        """更新书籍"""

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
                raise Error(404, "category_id", "无效的分类ID")
        if cover_image is not None:
            book.cover_image_path = save_cover_image(cover_image)
        book.save()
        return book

    @staticmethod
    def get_books() -> BaseManager[Book]:
        """获取书籍列表"""

        return Book.objects.all()

    @staticmethod
    def get_book(
        book_id: int,
    ) -> Book:
        """获取特定书籍"""

        return Book.objects.get(id=book_id)


class ChapterService:
    """章节服务类"""

    @staticmethod
    @transaction.atomic
    def create_chapter(
        book: Book,
        data: ChapterCreateInSchema,
    ) -> Chapter:
        """创建章节"""

        # 检查章数是否已存在
        if Chapter.objects.filter(book=book, chapter_number=data.chapter_number).exists():
            raise Error(400, "chapter_number", "该章数已存在")
        # 创建章节
        chapter: Chapter = Chapter.objects.create(
            book=book,
            chapter_number=data.chapter_number,
            title=data.title,
            content=data.content,
        )
        return chapter

    @staticmethod
    @transaction.atomic
    def delete_chapter(
        chapter: Chapter,
    ) -> None:
        """删除章节"""

        chapter.delete()
        return None

    @staticmethod
    @transaction.atomic
    def update_chapter(
        chapter: Chapter,
        data: ChapterUpdateInSchema,
    ) -> Chapter:
        """更新章节"""

        # 只更新提供的字段
        if data.chapter_number is not None:
            # 检查新章数是否已存在(排除自身)
            if Chapter.objects.filter(book=chapter.book, chapter_number=data.chapter_number).exclude(id=chapter.id).exists():
                raise Error(400, "chapter_number", "该章数已存在")
            chapter.chapter_number = data.chapter_number
        if data.title is not None:
            chapter.title = data.title
        if data.content is not None:
            chapter.content = data.content
        if data.status is not None:
            chapter.status = data.status
        chapter.save()
        return chapter

    @staticmethod
    def get_chapter(
        book_id: int,
        chapter_number: int,
    ) -> Chapter:
        """获取特定章节"""

        return Chapter.objects.get(book_id=book_id, chapter_number=chapter_number)

    @staticmethod
    def get_chapters(
        book: Book,
    ) -> BaseManager[Chapter]:
        """获取所有章节"""

        return Chapter.objects.filter(book=book)

    @staticmethod
    def get_chapters_by_range(
        book: Book,
        start: int,
        end: int,
    ) -> List[Chapter]:
        """获取指定范围内的章节"""

        return list(
            Chapter.objects.filter(
                book=book,
                chapter_number__gte=start,
                chapter_number__lt=end,
            ).order_by("chapter_number")
        )

    @staticmethod
    def get_chapter_content(
        chapter: Chapter,
    ) -> str:
        """获取文章中文本内容"""

        chapter_content: List[Dict] = chapter.content
        if not chapter_content:
            return ""
        # 过滤出 type 为 text 的项, 并按 index 排序
        text_items = [item for item in chapter_content if isinstance(item, dict) and item.get("type") == "text"]
        text_items.sort(key=lambda x: x.get("index", 0))
        # 合并所有文本内容
        extracted_text = "".join([str(item.get("content", "")) for item in text_items])
        return extracted_text


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
