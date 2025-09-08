# core/api.py
from ninja import NinjaAPI

from core.routers import router as core_router


api: NinjaAPI = NinjaAPI()

# 服务核心 API
api.add_router("/core", core_router)
