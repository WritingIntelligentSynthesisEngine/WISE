# ai/services.py
from typing import Any, Self, List

from book.services import BookService
from chains.generate_outline_chain import generate_outline
from chains.generate_chapter_chain import generate_chapter


class AiService:
    """AI 服务类"""

    pass


class BookAiService:
    """书籍 AI 服务类"""

    @staticmethod
    def generate_outline(
        llm: Any,
        book_id: int,
        current_number: int,
        context_size: int,
    ) -> str:
        """生成大纲"""

        # 获取设定
        book_settings = BookService.get_book(book_id).settings
        # 获取历史大纲
        previous_outlines: List[str] = []
        if current_number != 1:
            start_chapter: int = max(1, current_number - context_size)
            end_chapter: int = current_number
            for chapter in BookService.get_chapters(book_id, start_chapter, end_chapter):
                previous_outlines.append(chapter.outline)
        return generate_outline(llm, book_settings, current_number, previous_outlines)

    def generate_chapter(
        self: Self,
        llm: Any,
        book_id: int,
        current_number: int,
        context_size: int,
    ) -> str:
        """生成章节"""

        # 获取设定
        book_settings = BookService.get_book(book_id).settings
        outline = BookService.get_chapter(book_id, current_number).outline
        # 获取历史大纲和正文
        previous_outlines: List[str] = []
        previous_chapters: List[str] = []
        if current_number != 1:
            start_chapter: int = max(1, current_number - context_size)
            end_chapter: int = current_number
            for chapter in BookService.get_chapters(book_id, start_chapter, end_chapter):
                previous_outlines.append(chapter.outline)
                # 提取正文文本
                chapter_text: str = BookService.get_chapter_content(chapter)
                previous_chapters.append(chapter_text)
        return generate_chapter(llm, book_settings, current_number, previous_outlines, previous_chapters, outline)
