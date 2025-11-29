# core/endpoints.py
from typing import Tuple, Literal

from ninja import Router
from django.http import HttpRequest

from core.schemas import StatusOut
from core.services import CoreService


router: Router = Router(tags=["核心"])


@router.get(
    "/status",
    summary="服务状态检查",
    description="用于连通测试和基础状态检查，返回服务基本状态信息。",
    response={200: StatusOut},
)
def get_status(request: HttpRequest) -> Tuple[Literal[200], StatusOut]:
    """获取服务状态信息"""
    status_data = CoreService.get_service_status()
    return 200, StatusOut(**status_data)
