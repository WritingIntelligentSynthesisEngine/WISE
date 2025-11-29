# core/services.py
from typing import Dict, Any
from datetime import datetime


class CoreService:
    """核心业务逻辑服务"""

    @staticmethod
    def get_service_status() -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            "status": "healthy",
            "message": "服务运行正常",
            "timestamp": datetime.now(),
        }
