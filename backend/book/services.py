# book/services.py
from typing import List, Dict

from ninja import UploadedFile
from django.db import transaction
from utils.exception_util import Error
from django.db.models.manager import BaseManager
from django.contrib.auth.models import AbstractUser, AnonymousUser

from book.models import Category, Book, UserBookRelation, Chapter
from utils.file_util import save_cover_image, remove_unused_cover_image
from book.schemas import BookCreateInSchema, BookUpdateInSchema, ChapterCreateInSchema, ChapterUpdateInSchema


class BookService:
    """书籍服务类"""

    @staticmethod
    @transaction.atomic
    def create_book(
        user: AbstractUser | AnonymousUser,
        category: Category | None,
        data: BookCreateInSchema,
    ) -> Book:
        """创建书籍, 并且创建用户与书籍的作者关系, 如果有封面则保存在媒体目录"""

        # 创建书籍
        book: Book = Book.objects.create(
            category=category,
            title=data.title,
            description=data.description,
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
        # 尝试删除封面
        remove_unused_cover_image(cover_image_path)
        return None

    @staticmethod
    @transaction.atomic
    def delete_cover_image(
        book: Book,
    ) -> None:
        """移除书籍封面"""

        old_image_path: str = book.cover_image_path
        if old_image_path:
            # 清空数据库字段
            book.cover_image_path = ""
            book.save()
            # 尝试删除封面
            remove_unused_cover_image(old_image_path)
        return None

    @staticmethod
    @transaction.atomic
    def update_book(
        category: Category | None,
        book: Book,
        data: BookUpdateInSchema,
    ) -> Book:
        """更新书籍"""

        # 只更新提供的字段
        if data.title is not None:
            book.title = data.title
        if data.description is not None:
            book.description = data.description
        if data.attributes is not None:
            book.attributes = data.attributes
        if category is not None:
            book.category = category
        book.save()
        return book

    @staticmethod
    @transaction.atomic
    def update_cover_image(
        book: Book,
        cover_image: UploadedFile,
    ) -> Book:
        """更新书籍封面"""

        old_image_path: str = book.cover_image_path
        # 保存新封面
        new_image_path: str = save_cover_image(cover_image)
        book.cover_image_path = new_image_path
        book.save()
        # 如果存在旧封面且路径不同, 检查是否需要清理
        if old_image_path and old_image_path != new_image_path:
            remove_unused_cover_image(old_image_path)
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

    @staticmethod
    async def get_book_async(
        book_id: int,
    ) -> Book:
        """获取特定书籍(异步)"""

        return await Book.objects.aget(id=book_id)


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
    def get_chapters(
        book: Book,
    ) -> BaseManager[Chapter]:
        """获取所有章节"""

        return Chapter.objects.filter(book=book)

    @staticmethod
    def get_chapter(
        book: Book,
        chapter_number: int,
    ) -> Chapter:
        """获取特定章节"""

        return Chapter.objects.get(book_id=book.id, chapter_number=chapter_number)

    @staticmethod
    async def get_chapter_async(
        book: Book,
        chapter_number: int,
    ) -> Chapter:
        """获取特定章节(异步)"""

        return await Chapter.objects.aget(book_id=book.id, chapter_number=chapter_number)

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
