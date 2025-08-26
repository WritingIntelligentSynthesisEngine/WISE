# core/api.py
from ninja import NinjaAPI

from core.routers import router as core_router

api: NinjaAPI = NinjaAPI()

api.add_router("/core", core_router)
