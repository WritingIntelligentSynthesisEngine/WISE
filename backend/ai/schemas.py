# ai/schemas.py
from ninja import Schema


class GenerateOutlineInSchema(Schema):
    """生成大纲时的输入"""

    book_id: int
    chapter_number: int
    context_size: int = 3
