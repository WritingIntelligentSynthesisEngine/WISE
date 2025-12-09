# core/services.py
from typing import Any, Dict, Literal


class CoreService:
    """核心服务"""

    @staticmethod
    def get_service_status() -> Dict[Literal["data"], str]:
        """获取服务状态信息"""
        return {
            "data": "服务运行正常",
        }
