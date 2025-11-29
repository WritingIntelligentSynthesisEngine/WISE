# core/schemas.py
from ninja import Schema
from datetime import datetime


class StatusOut(Schema):
    """状态输出"""

    status: str
    message: str
    timestamp: datetime
