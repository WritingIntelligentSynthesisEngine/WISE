# book/services.py
from typing import List, Dict

from ninja.errors import HttpError

from book.models import Book, Chapter


class BookService:

    @staticmethod
    def get_book(
        book_id: int,
    ) -> Book:
        """获取特定书籍"""

        return Book.objects.get(id=book_id)

    @staticmethod
    def get_chapter(
        book_id: int,
        chapter_number: int,
    ) -> Chapter:
        """获取特定章节"""

        try:
            book: Book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            raise HttpError(404, "书籍不存在")
        # 获取章节
        try:
            return Chapter.objects.get(book_id=book_id, chapter_number=chapter_number)
        except Chapter.DoesNotExist:
            raise HttpError(404, "章节不存在")

    @staticmethod
    def get_chapters(
        book_id: int,
        start_chapter: int,
        end_chapter: int,
    ) -> List[Chapter]:
        """批量获取指定范围内的章节"""

        try:
            book: Book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            raise HttpError(404, "书籍不存在")
        # 批量获取章节
        chapters = Chapter.objects.filter(book_id=book_id, chapter_number__gte=start_chapter, chapter_number__lt=end_chapter).order_by("chapter_number")
        return list(chapters)

    @staticmethod
    def get_chapter_content(
        chapter: Chapter,
    ) -> str:
        """从文章中提取文本内容"""

        chapter_content: List[Dict] = chapter.content
        if not chapter_content:
            return ""
        # 过滤出 type 为 text 的项，并按 index 排序
        text_items = [item for item in chapter_content if isinstance(item, dict) and item.get("type") == "text"]
        text_items.sort(key=lambda x: x.get("index", 0))
        # 合并所有文本内容
        extracted_text = "".join([str(item.get("content", "")) for item in text_items])
        return extracted_text
