# ai/services.py
from typing import Any, List, Generator

from book.models import Book, Chapter
from book.services import ChapterService
from ai.chains.generate_outline_chain import generate_outline
from ai.chains.generate_chapter_chain import generate_chapter


class AiService:
    """AI 服务类"""

    pass


class BookAiService:
    """书籍 AI 服务类"""

    @staticmethod
    def generate_outline(
        llm: Any,
        book: Book,
        chapter: Chapter,
        context_size: int,
    ) -> Generator[str, None, None]:
        """生成大纲(流式)"""

        # 获取设定
        book_settings: str = book.settings
        # 获取当前章节数
        current_number: int = chapter.chapter_number
        # 获取历史大纲
        previous_outlines: List[str] = []
        if current_number != 1:
            start_chapter: int = max(1, current_number - context_size)
            end_chapter: int = current_number
            for chapter in ChapterService.get_chapters_by_range(book, start_chapter, end_chapter):
                previous_outlines.append(chapter.outline)
        # 调用流式生成函数并逐个返回 chunk
        for chunk in generate_outline(llm, book_settings, current_number, previous_outlines):
            yield chunk

    @staticmethod
    def generate_chapter(
        llm: Any,
        book: Book,
        chapter: Chapter,
        context_size: int,
    ) -> str:
        """生成章节"""

        # 获取设定
        book_settings: str = book.settings
        # 获取当前章节数
        current_number: int = chapter.chapter_number
        # 获取当前大纲
        outline: str = chapter.outline

        # 获取历史大纲和正文
        previous_outlines: List[str] = []
        previous_chapters: List[str] = []
        if current_number != 1:
            start_chapter: int = max(1, current_number - context_size)
            end_chapter: int = current_number
            for chapter in ChapterService.get_chapters_by_range(book, start_chapter, end_chapter):
                previous_outlines.append(chapter.outline)
                # 提取正文文本
                chapter_text: str = ChapterService.get_chapter_content(chapter)
                previous_chapters.append(chapter_text)
        return generate_chapter(llm, book_settings, current_number, previous_outlines, previous_chapters, outline)
