# book/schemas.py
from datetime import datetime
from typing import Any, Optional, List, Dict

from ninja import Schema


class BookCreateInSchema(Schema):
    """创建书籍时的输入"""

    category_id: Optional[int] = None
    title: str
    description: str = "无"
    attributes: Dict[str, Any] = {}


class BookUpdateInSchema(Schema):
    """更新书籍时的输入"""

    category_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


class BookOutSchema(Schema):
    """完整书籍的输出"""

    id: int
    category_id: Optional[int] = None
    title: str
    description: str
    cover_image_path: str
    create_time: datetime
    update_time: datetime
    status: str
    attributes: Dict[str, Any]


class ChapterCreateInSchema(Schema):
    """创建章节时的输入"""

    chapter_number: int
    title: str
    content: List[Dict[str, Any]] = []


class ChapterUpdateInSchema(Schema):
    """更新章节时的输入"""

    chapter_number: Optional[int] = None
    title: Optional[str] = None
    content: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class ChapterOutSchema(Schema):
    """完整章节的输出"""

    id: int
    book_id: int
    chapter_number: int
    title: str
    content: List[Dict[str, Any]]
    create_time: datetime
    update_time: datetime
    status: str
