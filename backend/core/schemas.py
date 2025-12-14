# core/schemas.py
from datetime import datetime
from typing import Optional, TypeVar, Generic, List

from ninja import Schema, Field


T = TypeVar("T")


class OutSchema(Schema, Generic[T]):
    """标准输出"""

    message: str = Field(default="success", description="消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    errors: Optional[List[ErrorDetailSchema]] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ErrorDetailSchema(Schema):
    """错误详情"""

    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(description="错误信息")
