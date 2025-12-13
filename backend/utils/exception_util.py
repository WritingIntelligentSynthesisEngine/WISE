# utils/exception_util.py
from typing import Self

from ninja.errors import HttpError
from ninja_extra import NinjaExtraAPI
from django.http import HttpRequest, HttpResponse

from core.schemas import OutSchema, ErrorDetailSchema


class Error(HttpError):
    """异常基类"""

    def __init__(self: Self, status_code: int, field: str, message: str) -> None:
        super().__init__(status_code, message)
        self.field = field


def register_exception_handlers(api: NinjaExtraAPI) -> None:
    """注册全局异常处理器"""

    @api.exception_handler(Error)
    def handle_core_exception(request: HttpRequest, exc: Error) -> HttpResponse:
        """处理默认异常"""

        error_response = OutSchema(data=None, errors=ErrorDetailSchema(field=exc.field, message=exc.message))
        return api.create_response(request, error_response, status=exc.status_code)
