# core/api.py
from ninja_extra import NinjaExtraAPI

from core.routers import router as core_router
from book.routers import router as book_router
from core.routers import NinjaJWTDefaultController


api: NinjaExtraAPI = NinjaExtraAPI(title="AllBookCloud API")

# 服务核心 API
api.add_router("/core", core_router)
# JWT API
api.register_controllers(NinjaJWTDefaultController)
# 书籍与文章 API
api.add_router("/book", book_router)
