# ai/endpoints.py
import json
from typing import Any, Generator

from ninja import Router
from pydantic import SecretStr
from django.conf import settings
from django.http import HttpRequest, StreamingHttpResponse
from django.contrib.auth.models import AbstractUser, AnonymousUser

from langchain_deepseek import ChatDeepSeek

from ai.llms import construct_llm
from core.schemas import OutSchema
from ai.services import BookAiService
from book.models import Book, Chapter
from book.permissions import can_view
from utils.exception_util import Error
from ai.schemas import GenerateOutlineInSchema
from utils.authentication_util import OptionalAuth
from book.services import BookService, ChapterService


router: Router = Router(tags=["AI"])


@router.post(
    "/aitools/generate-outline-tool",
    summary="生成书籍大纲",
    auth=OptionalAuth(),
    response={201: Any, 400: OutSchema[None], 403: OutSchema[None], 404: OutSchema[None], 500: OutSchema[None]},
)
def generate_outline(
    request: HttpRequest,
    data: GenerateOutlineInSchema,
) -> StreamingHttpResponse:
    """生成书籍大纲(流式)"""

    # 获取当前用户
    user: AbstractUser | AnonymousUser = request.user
    # 获取书籍
    try:
        book: Book = BookService.get_book(data.book_id)
    except Book.DoesNotExist:
        raise Error(404, "book_id", "书籍不存在")
    # 检查权限
    if not can_view(request.user, book):
        raise Error(403, "permission", "没有查看权限")
    # 获取章节
    try:
        chapter: Chapter = ChapterService.get_chapter(book, data.chapter_number)
    except Chapter.DoesNotExist:
        raise Error(404, "chapter_number", "章节不存在")
    # 获取用户的 API Key
    api_key: str | None = user.api_key  # pyright: ignore[reportAttributeAccessIssue]
    if api_key is None:
        raise Error(400, "api_key", "未设置 API Key")

    def event_stream() -> Generator[str, None, None]:
        """生成 SSE 流"""
        try:
            llm: ChatDeepSeek = construct_llm(SecretStr(secret_value=api_key))
            # 获取流式生成器
            outline_chunks: Generator[str, None, None] = BookAiService.generate_outline(
                llm=llm,
                book=book,
                chapter=chapter,
                context_size=data.context_size,
            )
            # 发送每个 chunk 作为 SSE 事件
            for chunk in outline_chunks:
                if chunk:
                    # 正确格式化 SSE 数据
                    # 将 chunk 编码为 JSON 字符串以确保正确转义
                    data_json = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"data: {data_json}\n\n"
            # 发送完成事件
            yield 'event: complete\ndata: {"status": "done"}\n\n'
        except Exception as e:
            # 发送错误事件
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
    }
    if not settings.DEBUG:
        headers["Connection"] = "keep-alive"

    return StreamingHttpResponse(
        event_stream(),  # pyright: ignore[reportArgumentType]
        content_type="text/event-stream",
        headers=headers,
    )
