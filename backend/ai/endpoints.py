# ai/endpoints.py
from typing import Any, AsyncGenerator

from ninja import Router
from pydantic import SecretStr
from django.http import HttpRequest, StreamingHttpResponse
from django.contrib.auth.models import AbstractUser, AnonymousUser

from langchain_deepseek import ChatDeepSeek

from ai.llms import construct_llm
from core.schemas import OutSchema
from ai.services import BookAiService
from book.models import Book, Chapter
from book.permissions import can_view
from asgiref.sync import sync_to_async
from utils.exception_util import Error
from ai.schemas import GenerateOutlineInSchema
from utils.authentication_util import OptionalAuth
from utils.sse_util import create_sse_response
from book.services import BookService, ChapterService


router: Router = Router(tags=["AI"])


@router.post(
    "/aitools/generate-outline-tool",
    summary="生成书籍大纲",
    auth=OptionalAuth(),
    response={201: Any, 400: OutSchema[None], 403: OutSchema[None], 404: OutSchema[None], 500: OutSchema[None]},
)
async def generate_outline(
    request: HttpRequest,
    data: GenerateOutlineInSchema,
) -> StreamingHttpResponse:
    """生成书籍大纲(流式)"""

    # 获取当前用户
    user: AbstractUser | AnonymousUser = request.user
    # 获取书籍
    try:
        book: Book = await BookService.get_book_async(data.book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 检查权限
    if not sync_to_async(can_view)(request.user, book):
        raise Error(403, "permission", "没有查看权限")
    # 获取章节
    try:
        chapter: Chapter = await ChapterService.get_chapter_async(book, data.chapter_number)
    except Chapter.DoesNotExist:
        raise Error(404, "chapter_number", "章节不存在")
    # 获取用户的 API Key
    api_key: str | None = user.api_key  # pyright: ignore[reportAttributeAccessIssue]
    if api_key is None:
        raise Error(400, "api_key", "未设置 API Key")

    async def outline_generator() -> AsyncGenerator[str, None]:
        """生成大纲内容的异步生成器"""

        llm: ChatDeepSeek = await construct_llm(SecretStr(secret_value=api_key))
        outline_chunks: AsyncGenerator[str, None] = BookAiService.generate_outline(
            llm=llm,
            book=book,
            chapter=chapter,
            context_size=data.context_size,
        )
        async for chunk in outline_chunks:
            yield chunk

    return create_sse_response(outline_generator())
