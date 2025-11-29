# backend/api.py
from ninja import NinjaAPI

from core.endpoints import router as core_router


api: NinjaAPI = NinjaAPI()

# 注册路由
api.add_router("/", core_router)
