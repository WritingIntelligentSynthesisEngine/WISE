# utils/sse_util.py
import json
from typing import AsyncGenerator

from django.conf import settings
from django.http import StreamingHttpResponse


async def _event_stream(generator: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
    """内部事件流生成器, 将字符串生成器转换为 SSE 格式"""

    try:
        async for chunk in generator:
            if chunk:
                # 将 chunk 编码为 JSON 字符串以确保正确转义
                data_json = json.dumps({"content": chunk}, ensure_ascii=False)
                yield f"data: {data_json}\n\n".encode("utf-8")
        # 发送完成事件
        yield "data: [DONE]\n\n".encode("utf-8")
    except Exception as e:
        # 发送错误事件
        error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
        yield f"event: error\ndata: {error_data}\n\n".encode("utf-8")


def create_sse_response(generator: AsyncGenerator[str, None]) -> StreamingHttpResponse:
    """
    创建 SSE 响应

    :param generator: 异步字符串生成器, 每个字符串将作为 SSE 事件的 data 字段发送
    :type generator: AsyncGenerator[str, None]
    :return: 配置好的 SSE 响应
    :rtype: StreamingHttpResponse
    """

    headers = {
        "Cache-Control": "no-cache",
    }
    if not settings.DEBUG:
        headers.update(
            {
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
        )
    return StreamingHttpResponse(
        _event_stream(generator),
        content_type="text/event-stream",
        headers=headers,
    )
