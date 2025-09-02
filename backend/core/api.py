# core/api.py
from ninja import NinjaAPI

from core.routers import router as core_router
from book.routers import router as book_router

api: NinjaAPI = NinjaAPI(title="AllBookCloud API")

api.add_router("/core", core_router)
api.add_router("/book", book_router)
